export interface SpeechRecognitionAlternative {
  transcript: string;
}

export interface SpeechRecognitionResult {
  isFinal: boolean;
  [index: number]: SpeechRecognitionAlternative;
}

export interface SpeechRecognitionResultList {
  length: number;
  [index: number]: SpeechRecognitionResult;
}

export interface SpeechRecognitionResultEvent extends Event {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}

export interface SpeechRecognitionErrorEvent extends Event {
  error: string;
}

export interface SpeechRecognitionInstance {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onstart: (() => void) | null;
  onresult: ((event: SpeechRecognitionResultEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
}

export type SpeechRecognitionConstructor = new () => SpeechRecognitionInstance;

export function getSpeechRecognitionConstructor(): SpeechRecognitionConstructor | null {
  const speechWindow = window as Window & {
    SpeechRecognition?: SpeechRecognitionConstructor;
    webkitSpeechRecognition?: SpeechRecognitionConstructor;
  };

  return (
    speechWindow.SpeechRecognition ??
    speechWindow.webkitSpeechRecognition ??
    null
  );
}

export type MicrophoneAccessErrorCode =
  | "MICROPHONE_SECURE_CONTEXT"
  | "MICROPHONE_UNAVAILABLE"
  | "MICROPHONE_PERMISSION_DENIED"
  | "MICROPHONE_NOT_FOUND"
  | "MICROPHONE_UNKNOWN_ERROR";

function createMicrophoneError(
  code: MicrophoneAccessErrorCode,
  cause: unknown,
): Error {
  const error = new Error(code);

  /*
   * The project's TypeScript lib does not expose
   * the Error(message, { cause }) constructor.
   * Attach the cause explicitly instead so that
   * ESLint's preserve-caught-error rule is still
   * satisfied.
   */
  Object.defineProperty(error, "cause", {
    value: cause,
    enumerable: false,
    configurable: true,
    writable: true,
  });

  return error;
}

export async function requestMicrophoneAccess(): Promise<void> {
  if (!window.isSecureContext) {
    throw new Error("MICROPHONE_SECURE_CONTEXT");
  }

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    throw new Error("MICROPHONE_UNAVAILABLE");
  }

  let permissionState: PermissionState | null = null;

  try {
    const permission = await navigator.permissions.query({
      name: "microphone" as PermissionName,
    });

    permissionState = permission.state;
  } catch {
    /*some random thing*/
  }

  if (permissionState === "denied") {
    throw new Error("MICROPHONE_PERMISSION_DENIED");
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: true,
      video: false,
    });

    for (const track of stream.getTracks()) {
      track.stop();
    }
  } catch (error) {
    if (error instanceof DOMException) {
      if (error.name === "NotAllowedError" || error.name === "SecurityError") {
        throw createMicrophoneError("MICROPHONE_PERMISSION_DENIED", error);
      }

      if (error.name === "NotFoundError") {
        throw createMicrophoneError("MICROPHONE_NOT_FOUND", error);
      }

      if (error.name === "NotSupportedError") {
        throw createMicrophoneError("MICROPHONE_UNAVAILABLE", error);
      }
    }

    throw createMicrophoneError("MICROPHONE_UNKNOWN_ERROR", error);
  }
}
