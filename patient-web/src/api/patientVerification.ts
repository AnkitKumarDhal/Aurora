import { apiRequest } from "./client";

export interface VerificationOtpChallenge {
  challenge_id: string;
  masked_destination: string;
  expires_in_seconds: number;
  demo_otp: string | null;
}

export interface PatientVerificationResult {
  verification_token: string;
  status: "VERIFIED";
  expires_in_seconds: number;
}

export async function requestPatientVerificationOtp(
  draftId: string,
  method: "ABHA" | "AADHAAR",
  identifier: string,
): Promise<VerificationOtpChallenge> {
  const response = await apiRequest<{
    data: VerificationOtpChallenge;
  }>("/identity/otp", {
    method: "POST",
    body: JSON.stringify({
      draft_id: draftId,
      method,
      identifier,
    }),
  });

  return response.data;
}

export async function verifyPatientIdentityOtp(
  draftId: string,
  challengeId: string,
  otp: string,
): Promise<PatientVerificationResult> {
  const response = await apiRequest<{
    data: PatientVerificationResult;
  }>("/identity/otp/verify", {
    method: "POST",
    body: JSON.stringify({
      draft_id: draftId,
      challenge_id: challengeId,
      otp,
    }),
  });

  return response.data;
}
