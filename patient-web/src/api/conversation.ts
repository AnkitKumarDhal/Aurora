import { apiRequest } from "./client";

export type ConversationInputType = "AUDIO" | "GUIDED_INPUT" | "TEXT";

export interface ConversationTurn {
  turn_id: string;
  session_id: string;
  speaker: string;
  input_type: ConversationInputType;
  content: string | null;
  language: string | null;
  media_reference: string | null;
  created_at: string;
}

interface ConversationTurnResponse {
  data: ConversationTurn;
}

export async function submitConversationTurn(
  sessionId: string,
  inputType: ConversationInputType,
  content: string,
  language: string,
): Promise<ConversationTurn> {
  const response = await apiRequest<ConversationTurnResponse>(
    `/sessions/${encodeURIComponent(sessionId)}/conversation/turns`,
    {
      method: "POST",
      body: JSON.stringify({
        input_type: inputType,
        content,
        language,
      }),
    },
  );

  return response.data;
}
