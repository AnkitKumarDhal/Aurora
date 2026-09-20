import { apiRequest } from "./client";

export interface PatientIntakeCompletionResponse {
  session_id: string;
  status: string;
  queue_entry_id: string;
  doctor_id: string | null;
}

export async function completePatientIntake(
  sessionId: string,
  draftId: string,
  verificationToken: string,
  identityMethod: "ABHA" | "AADHAAR",
  identityIdentifier: string,
): Promise<PatientIntakeCompletionResponse> {
  const response = await apiRequest<{
    data: PatientIntakeCompletionResponse;
  }>("/patient-intake/complete", {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      draft_id: draftId,
      verification_token: verificationToken,
      identity_method: identityMethod,
      identity_identifier: identityIdentifier,
    }),
  });

  return response.data;
}
