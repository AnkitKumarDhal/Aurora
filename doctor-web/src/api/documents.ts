import type { DocumentExtraction } from "@/types/api";
import { apiBlobRequest, apiRequest } from "./client";

export async function getDocumentExtraction(
  sessionId: string,
  documentId: string,
): Promise<DocumentExtraction | null> {
  const response = await apiRequest<{
    data: DocumentExtraction | null;
  }>(
    `/sessions/${encodeURIComponent(sessionId)}/documents/${encodeURIComponent(
      documentId,
    )}/extraction`,
  );

  return response.data;
}

export async function getDocumentFile(
  sessionId: string,
  documentId: string,
): Promise<Blob> {
  return apiBlobRequest(
    `/sessions/${encodeURIComponent(sessionId)}/documents/${encodeURIComponent(
      documentId,
    )}/file`,
  );
}
