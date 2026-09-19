import { apiRequest } from "./client";

export type InterviewInputType = "AUDIO" | "GUIDED_INPUT" | "TEXT";

export interface InterviewTurnResult {
  turn_id: string;
  session_id: string;
  speaker: string;
  input_type: InterviewInputType;
  content: string;
  language: string | null;
  created_at: string;
  assistant_response: string | null;
  next_question: string | null;
  completed: boolean;
  topic: string;
  known_fields: Record<string, unknown>;
  extracted_fields: Record<string, unknown>;
  negative_fields: string[];
  red_flags: string[];
  ai_used: boolean;
}

export interface InterviewState {
  session_id: string;
  topic: string;
  known_fields: Record<string, unknown>;
  patient_turns: number;
  next_question: string | null;
  completed: boolean;
  red_flags: string[];
  ai_enabled: boolean;
}

export interface PreparedInterviewSession {
  session_id: string;
  status: string;
  verification_status: string;
  consent_status: string;
}

export async function prepareInterviewSession(
  draftId: string,
  verificationToken: string,
  identityMethod: "ABHA" | "AADHAAR",
  identityIdentifier: string,
): Promise<PreparedInterviewSession> {
  const response = await apiRequest<{
    data: PreparedInterviewSession;
  }>("/patient-intake/interview/session", {
    method: "POST",
    body: JSON.stringify({
      draft_id: draftId,
      verification_token: verificationToken,
      identity_method: identityMethod,
      identity_identifier: identityIdentifier,
      department_id: "general-medicine",
    }),
  });

  return response.data;
}

export async function getInterviewState(
  sessionId: string,
): Promise<InterviewState> {
  const response = await apiRequest<{ data: InterviewState }>(
    `/sessions/${encodeURIComponent(sessionId)}/interview`,
  );

  return response.data;
}

export async function submitInterviewTurn(
  sessionId: string,
  draftId: string,
  clientTurnId: string,
  inputType: InterviewInputType,
  content: string,
  language: string,
): Promise<InterviewTurnResult> {
  const response = await apiRequest<{
    data: InterviewTurnResult;
  }>(`/sessions/${encodeURIComponent(sessionId)}/interview/turns`, {
    method: "POST",
    body: JSON.stringify({
      draft_id: draftId,
      client_turn_id: clientTurnId,
      input_type: inputType,
      content,
      language,
    }),
  });

  return response.data;
}

export async function finalizeInterview(sessionId: string): Promise<{
  session_id: string;
  status: string;
  summary: Record<string, unknown>;
  triage: Record<string, unknown>;
}> {
  const response = await apiRequest<{
    data: {
      session_id: string;
      status: string;
      summary: Record<string, unknown>;
      triage: Record<string, unknown>;
    };
  }>(`/sessions/${encodeURIComponent(sessionId)}/interview/finalize`, {
    method: "POST",
  });

  return response.data;
}
