import type { DocumentExtraction } from "@/types/api";
import { apiRequest } from "./client";

export async function getDocumentExtraction(
  sessionId: string,
  documentId: string,
): Promise<DocumentExtraction | null> {
  const response = await apiRequest<{
    data: DocumentExtraction | null;
  }>(`/sessions/${sessionId}/documents/${documentId}/extraction`);

  return response.data;
}
