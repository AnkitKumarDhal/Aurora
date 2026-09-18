import { apiRequest } from "./client";

export interface ConsentInformation {
  version: string;
  status: string;
  text: string;
  audio_available: boolean;
  supported_languages: string[];
}

export interface ConsentResponse {
  version: string;
  consent_status: string;
  recorded_at: string;
}

export async function getConsentInformation(
  sessionId: string,
): Promise<ConsentInformation> {
  const response = await apiRequest<{ data: ConsentInformation }>(
    `/sessions/${encodeURIComponent(sessionId)}/consent`,
  );

  return response.data;
}

export async function recordConsent(
  sessionId: string,
  version: string,
  granted: boolean,
): Promise<ConsentResponse> {
  const response = await apiRequest<{ data: ConsentResponse }>(
    `/sessions/${encodeURIComponent(sessionId)}/consent`,
    {
      method: "POST",
      body: JSON.stringify({
        version,
        granted,
      }),
    },
  );

  return response.data;
}
