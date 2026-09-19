import { apiRequest } from "./client";

export interface ConsentInformation {
  version: string;
  status: string;
  text: string;
  audio_available: boolean;
  supported_languages: string[];
}

export interface ConsentRecordResponse {
  version: string;
  consent_status: string;
  recorded_at: string;
}

export async function getConsentInformation(): Promise<ConsentInformation> {
  const response = await apiRequest<{ data: ConsentInformation }>(
    "/consent-information",
  );

  return response.data;
}

export async function recordConsent(
  sessionId: string,
  version: string,
  method: "ABHA" | "AADHAAR",
  identifier: string,
): Promise<ConsentRecordResponse> {
  const response = await apiRequest<{
    data: ConsentRecordResponse;
  }>(`/sessions/${encodeURIComponent(sessionId)}/consent`, {
    method: "POST",
    body: JSON.stringify({
      version,
      granted: true,
      method,
      identifier,
    }),
  });

  return response.data;
}
