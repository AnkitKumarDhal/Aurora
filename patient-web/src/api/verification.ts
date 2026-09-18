import { apiRequest } from "./client";

export interface VerificationResponse {
  verification_id: string;
  status: string;
  patient_id: string | null;
}

interface VerificationRequest {
  method: string;
  identifier: string;
}

export async function verifyPatient(
  sessionId: string,
  method: string,
  identifier: string,
): Promise<VerificationResponse> {
  const response = await apiRequest<{ data: VerificationResponse }>(
    `/sessions/${encodeURIComponent(sessionId)}/verification`,
    {
      method: "POST",
      body: JSON.stringify({
        method,
        identifier,
      } satisfies VerificationRequest),
    },
  );

  return response.data;
}
