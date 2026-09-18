import { apiRequest } from "./client";

export interface ClinicalSession {
  session_id: string;
  patient_id: string;
  department_id: string;
  status: string;
  verification_status: string;
  consent_status: string;
  created_at: string;
  updated_at: string;
}

interface CreateSessionResponse {
  data: ClinicalSession;
}

export async function createSession(
  departmentId = "general-medicine",
): Promise<ClinicalSession> {
  const response = await apiRequest<CreateSessionResponse>("/sessions", {
    method: "POST",
    body: JSON.stringify({
      department_id: departmentId,
    }),
  });

  return response.data;
}

export async function getSession(sessionId: string): Promise<ClinicalSession> {
  const response = await apiRequest<{ data: ClinicalSession }>(
    `/sessions/${encodeURIComponent(sessionId)}`,
  );

  return response.data;
}
