import type { QueueActionResponse } from "@/types/api";
import { apiRequest } from "./client";

async function runQueueAction(
  sessionId: string,
  queueEntryId: string,
  action: "call" | "start-consultation" | "complete",
): Promise<QueueActionResponse> {
  const response = await apiRequest<{ data: QueueActionResponse }>(
    `/sessions/${sessionId}/queue/${queueEntryId}/${action}`,
    {
      method: "POST",
    },
  );

  return response.data;
}

export async function callPatient(
  sessionId: string,
  queueEntryId: string,
): Promise<QueueActionResponse> {
  return runQueueAction(sessionId, queueEntryId, "call");
}

export async function startConsultation(
  sessionId: string,
  queueEntryId: string,
): Promise<QueueActionResponse> {
  return runQueueAction(sessionId, queueEntryId, "start-consultation");
}

export async function completeConsultation(
  sessionId: string,
  queueEntryId: string,
): Promise<QueueActionResponse> {
  return runQueueAction(sessionId, queueEntryId, "complete");
}
