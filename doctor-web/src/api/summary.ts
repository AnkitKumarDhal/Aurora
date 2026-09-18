import type { ClinicalSummary } from "@/types/api";
import { apiRequest } from "./client";

export interface ClinicalSummaryUpdateRequest {
  chief_complaint?: string | null;
  history_of_present_illness?: string | null;
  past_medical_history?: string[];
  medications?: string[];
  allergies?: string[];
}

export async function updateSummary(
  sessionId: string,
  updates: ClinicalSummaryUpdateRequest,
): Promise<ClinicalSummary> {
  const response = await apiRequest<{ data: ClinicalSummary }>(
    `/sessions/${sessionId}/summary`,
    {
      method: "PATCH",
      body: JSON.stringify(updates),
    },
  );

  return response.data;
}

export async function confirmSummary(
  sessionId: string,
): Promise<ClinicalSummary> {
  const response = await apiRequest<{ data: ClinicalSummary }>(
    `/sessions/${sessionId}/summary/confirm`,
    {
      method: "POST",
    },
  );

  return response.data;
}
