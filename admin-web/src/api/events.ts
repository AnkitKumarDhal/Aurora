import { getAccessToken } from "@/auth/auth";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export type AuroraEventType =
  | "QUEUE_UPDATED"
  | "ASSIGNMENT_UPDATED"
  | "PROMOTION_UPDATED";

export interface AuroraEvent {
  id: string;
  type: AuroraEventType;
  department_id: string;
  entity_id: string | null;
  timestamp: string;
}

type EventHandler = (event: AuroraEvent) => void;
type ErrorHandler = (error: Error) => void;

function isAuroraEventType(value: string): value is AuroraEventType {
  return (
    value === "QUEUE_UPDATED" ||
    value === "ASSIGNMENT_UPDATED" ||
    value === "PROMOTION_UPDATED"
  );
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

async function consumeSse(
  response: Response,
  onEvent: EventHandler,
): Promise<void> {
  if (!response.body) {
    throw new Error("SSE response has no body.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  let buffer = "";
  let eventName = "";
  let eventId = "";
  let dataLines: string[] = [];

  const dispatch = (): void => {
    const currentEventName = eventName;
    const currentEventId = eventId;
    const rawData = dataLines.join("\n");

    eventName = "";
    eventId = "";
    dataLines = [];

    if (!currentEventName || !rawData) {
      return;
    }

    if (!isAuroraEventType(currentEventName)) {
      return;
    }

    try {
      const payload = JSON.parse(rawData) as AuroraEvent;

      onEvent({
        ...payload,
        id: payload.id || currentEventId,
        type: currentEventName,
      });
    } catch {
      return;
    }
  };

  const processLine = (line: string): void => {
    const normalized = line.endsWith("\r") ? line.slice(0, -1) : line;

    if (normalized === "") {
      dispatch();
      return;
    }

    if (normalized.startsWith(":")) {
      return;
    }

    const separator = normalized.indexOf(":");

    if (separator === -1) {
      return;
    }

    const field = normalized.slice(0, separator);
    let value = normalized.slice(separator + 1);

    if (value.startsWith(" ")) {
      value = value.slice(1);
    }

    if (field === "event") {
      eventName = value;
    } else if (field === "id") {
      eventId = value;
    } else if (field === "data") {
      dataLines.push(value);
    }
  };

  while (true) {
    const { done, value } = await reader.read();

    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      processLine(line);
    }
  }

  buffer += decoder.decode();

  if (buffer) {
    processLine(buffer);
  }

  dispatch();
}

export function subscribeToEvents(
  departmentId: string,
  onEvent: EventHandler,
  onError?: ErrorHandler,
): () => void {
  let stopped = false;
  let controller: AbortController | null = null;

  const connect = async (): Promise<void> => {
    let retryDelay = 1000;

    while (!stopped) {
      controller = new AbortController();

      try {
        const token = getAccessToken();

        if (!token) {
          return;
        }

        const response = await fetch(
          `${API_BASE_URL}/events/stream?department_id=${encodeURIComponent(departmentId)}`,
          {
            method: "GET",
            headers: {
              Accept: "text/event-stream",
              Authorization: `Bearer ${token}`,
            },
            cache: "no-store",
            signal: controller.signal,
          },
        );

        if (response.status === 401 || response.status === 403) {
          onError?.(
            new Error(
              "The event stream is not authorized. Please sign in again.",
            ),
          );
          return;
        }

        if (!response.ok) {
          throw new Error(`Event stream failed with HTTP ${response.status}`);
        }

        retryDelay = 1000;

        await consumeSse(response, onEvent);
      } catch (error) {
        if (stopped) {
          return;
        }

        onError?.(
          error instanceof Error
            ? error
            : new Error("Event stream disconnected."),
        );
      }

      if (stopped) {
        return;
      }

      await sleep(retryDelay);

      retryDelay = Math.min(retryDelay * 2, 10000);
    }
  };

  void connect();

  return () => {
    stopped = true;
    controller?.abort();
  };
}
