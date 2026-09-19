import { apiRequest } from "./client";
import type {
  PatientDraftConversationInputType,
  PatientDraftIdentityMethod,
} from "@/lib/patientDraft";

export interface ClinicalIntelligenceTurnResponse {
  turn_id: string;
  session_id: string;
  speaker: string;
  input_type: PatientDraftConversationInputType;
  content: string;
  language: string | null;
  created_at: string;
  assistant_response: string | null;
  next_question: string | null;
  completed: boolean;
}

interface ClinicalIntelligenceTurnApiResponse {
  data: ClinicalIntelligenceTurnResponse;
}

interface ClinicalIntelligenceTurnRequest {
  draft_id: string;
  local_id: string;
  verification_token: string;
  identity_method: PatientDraftIdentityMethod;
  identity_identifier: string;
  input_type: PatientDraftConversationInputType;
  content: string;
  language: string;
}

export async function processClinicalIntelligenceTurn(
  sessionId: string,
  request: ClinicalIntelligenceTurnRequest,
): Promise<ClinicalIntelligenceTurnResponse> {
  const response = await apiRequest<ClinicalIntelligenceTurnApiResponse>(
    `/sessions/${encodeURIComponent(sessionId)}/clinical-intelligence/turns`,
    {
      method: "POST",
      body: JSON.stringify(request),
    },
  );

  return response.data;
}
