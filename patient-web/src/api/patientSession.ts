import { apiRequest } from "./client";
import type { PatientDraftIdentityMethod } from "@/lib/patientDraft";

export interface PatientSessionResponse {
  session_id: string;
  status: string;
  verification_status: string;
  consent_status: string;
}

interface PreparePatientSessionResponse {
  data: PatientSessionResponse;
}

export async function preparePatientSession(
  draftId: string,
  verificationToken: string,
  identityMethod: PatientDraftIdentityMethod,
  identityIdentifier: string,
  consentVersion: string,
): Promise<PatientSessionResponse> {
  const response = await apiRequest<PreparePatientSessionResponse>(
    "/patient-intake/session/prepare",
    {
      method: "POST",
      body: JSON.stringify({
        draft_id: draftId,
        verification_token: verificationToken,
        identity_method: identityMethod,
        identity_identifier: identityIdentifier,
        consent_version: consentVersion,
        department_id: "general-medicine",
      }),
    },
  );

  return response.data;
}
