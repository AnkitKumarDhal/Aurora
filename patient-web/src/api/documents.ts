import { apiRequest } from "./client";

export type DocumentType =
  | "IMAGING_REPORT"
  | "LAB_REPORT"
  | "MEDICAL_RECORD"
  | "OTHER"
  | "PRESCRIPTION";

export type DocumentStatus = "FAILED" | "PROCESSED" | "PROCESSING" | "UPLOADED";

export interface PatientDocument {
  document_id: string;
  session_id: string;
  filename: string;
  document_type: DocumentType;
  content_type: string;
  size_bytes: number;
  storage_reference: string;
  status: DocumentStatus;
  created_at: string;
  updated_at: string;
}

interface DocumentResponse {
  data: PatientDocument;
}

export async function uploadDocument(
  sessionId: string,
  file: File,
  documentType: DocumentType = "OTHER",
): Promise<PatientDocument> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiRequest<DocumentResponse>(
    `/sessions/${encodeURIComponent(sessionId)}/documents?document_type=${encodeURIComponent(documentType)}`,
    {
      method: "POST",
      body: formData,
    },
  );

  return response.data;
}
