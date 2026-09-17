import type {
  DoctorQueueEntry,
  DoctorQueueResponse,
  QueueActionResponse,
} from "@/types/api";
import { apiRequest } from "./client";

export async function getDoctorQueue(): Promise<DoctorQueueResponse> {
  const response = await apiRequest<{ data: DoctorQueueResponse }>(
    "/doctors/me/queue",
  );

  return response.data;
}

export async function getDoctorQueueEntry(
  sessionId: string,
): Promise<DoctorQueueEntry | null> {
  const queue = await getDoctorQueue();

  return queue.entries.find((entry) => entry.session_id === sessionId) ?? null;
}

export async function getQueueEntry(
  queueEntryId: string,
): Promise<QueueActionResponse["queue_entry"]> {
  const response = await apiRequest<{
    data: QueueActionResponse["queue_entry"];
  }>(`/queue/${queueEntryId}`);

  return response.data;
}
