import { apiRequest } from "./client";

export interface VerificationOtpChallenge {
  challenge_id: string;
  masked_destination: string;
  expires_in_seconds: number;
  demo_otp: string | null;
}

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

interface VerificationOtpRequest {
  challenge_id: string;
  otp: string;
}

export async function requestIdentityOtp(
  sessionId: string,
  method: string,
  identifier: string,
): Promise<VerificationOtpChallenge> {
  const response = await apiRequest<{
    data: VerificationOtpChallenge;
  }>(`/sessions/${encodeURIComponent(sessionId)}/verification/otp`, {
    method: "POST",
    body: JSON.stringify({
      method,
      identifier,
    } satisfies IdentificationRequest),
  });

  return response.data;
}

export async function verifyPatientOtp(
  sessionId: string,
  challengeId: string,
  otp: string,
): Promise<PatientIdentificationResponse> {
  const response = await apiRequest<{
    data: PatientIdentificationResponse;
  }>(`/sessions/${encodeURIComponent(sessionId)}/verification`, {
    method: "POST",
    body: JSON.stringify({
      challenge_id: challengeId,
      otp,
    } satisfies VerificationOtpRequest),
  });

  return response.data;
}
