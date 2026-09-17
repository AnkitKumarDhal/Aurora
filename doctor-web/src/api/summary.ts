import type { ClinicalSummary } from "@/types/api";
import { apiRequest } from "./client";

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
