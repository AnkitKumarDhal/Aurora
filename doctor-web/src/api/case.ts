import type { DoctorCaseResponse } from "@/types/api";
import { apiRequest } from "./client";

export async function getDoctorCase(
  sessionId: string,
): Promise<DoctorCaseResponse> {
  const response = await apiRequest<{ data: DoctorCaseResponse }>(
    `/doctors/me/cases/${sessionId}`,
  );
  return response.data;
}
