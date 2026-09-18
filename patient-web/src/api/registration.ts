import { apiRequest } from "./client";
import type { PatientDraft, PatientDraftDocument } from "@/lib/patientDraft";

export interface RegistrationResponse {
  session_id: string;
  patient_id: string;
  status: string;
  visit_type: "FIRST_VISIT" | "RETURNING_VISIT";
}

export async function submitPatientRegistration(
  draft: PatientDraft,
  documents: PatientDraftDocument[],
): Promise<RegistrationResponse> {
  const formData = new FormData();

  formData.append("draft", JSON.stringify(draft));

  formData.append(
    "documents",
    JSON.stringify(
      documents.map((document) => ({
        local_id: document.local_id,
        filename: document.filename,
        content_type: document.content_type,
        size_bytes: document.size_bytes,
        document_type: document.document_type,
      })),
    ),
  );

  for (const document of documents) {
    formData.append("files", document.file, document.filename);
  }

  const response = await apiRequest<{
    data: RegistrationResponse;
  }>("/patient-intake/submit", {
    method: "POST",
    body: formData,
  });

  return response.data;
}
