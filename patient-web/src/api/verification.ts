import { apiRequest } from "./client";

export interface PatientIdentificationResponse {
  verification_id: string;
  status: string;
  patient_id: string | null;
  existing_patient: boolean;
  visit_type: "FIRST_VISIT" | "RETURNING_VISIT";
}

interface IdentificationRequest {
  method: string;
  identifier: string;
}

export async function identifyPatient(
  sessionId: string,
  method: string,
  identifier: string,
): Promise<PatientIdentificationResponse> {
  const response = await apiRequest<{
    data: PatientIdentificationResponse;
  }>(`/sessions/${encodeURIComponent(sessionId)}/verification`, {
    method: "POST",
    body: JSON.stringify({
      method,
      identifier,
    } satisfies IdentificationRequest),
  });

  return response.data;
}
