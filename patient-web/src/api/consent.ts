import { apiRequest } from "./client";

export interface ConsentInformation {
  version: string;
  status: string;
  text: string;
  audio_available: boolean;
  supported_languages: string[];
}

export async function getConsentInformation(): Promise<ConsentInformation> {
  const response = await apiRequest<{
    data: ConsentInformation;
  }>("/consent-information");

  return response.data;
}
