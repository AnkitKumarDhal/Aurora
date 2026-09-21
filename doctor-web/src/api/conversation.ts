import type { ConversationHistoryResponse } from "@/types/api";
import { apiRequest } from "./client";

export async function getConversationHistory(
  sessionId: string,
): Promise<ConversationHistoryResponse> {
  const response = await apiRequest<{
    data: ConversationHistoryResponse;
  }>(`/sessions/${encodeURIComponent(sessionId)}/conversation/turns`);

  return response.data;
}
