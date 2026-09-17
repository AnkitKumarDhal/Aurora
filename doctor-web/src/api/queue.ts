import type { DoctorQueueResponse } from "@/types/api";
import { apiRequest } from "./client";

export async function getDoctorQueue(): Promise<DoctorQueueResponse> {
  const response = await apiRequest<{ data: DoctorQueueResponse }>(
    "/doctors/me/queue",
  );
  return response.data;
}
