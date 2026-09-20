import { apiRequest } from "./client";

export interface AdminDashboardStats {
  patients: number;
  waiting: number;
  in_consultation: number;
  doctors: number;
}

export interface AdminDashboardDoctor {
  doctor_id: string;
  display_name: string;
  status: string;
  assigned_count: number;
}

export interface AdminDashboardPatient {
  queue_entry_id: string;
  session_id: string;
  patient_id: string;
  display_name: string;
  age: number | null;
  urgency_level: number | null;
  priority_score: number | null;
  queue_status: string;
  doctor_id: string | null;
  doctor_name: string | null;
  chief_complaint: string | null;
  queued_at: string | null;
  waiting_time_seconds: number | null;
}

export interface AdminDashboardPromotion {
  promotion_request_id: string;
  queue_entry_id: string;
  patient_id: string;
  patient_name: string;
  current_doctor_id: string | null;
  current_doctor_name: string | null;
  target_doctor_id: string;
  target_doctor_name: string;
  reason: string;
  status: string;
  decision_deadline: string;
}

export interface AdminDashboard {
  department_id: string;
  stats: AdminDashboardStats;
  doctors: AdminDashboardDoctor[];
  patients: AdminDashboardPatient[];
  promotions: AdminDashboardPromotion[];
}

export interface ReassignmentResponse {
  queue_entry_id: string;
  session_id: string;
  previous_doctor_id: string | null;
  doctor_id: string;
  assignment_id: string;
}

export interface PromotionResponse {
  promotion_request_id: string;
  queue_entry_id: string;
  target_doctor_id: string;
  reason: string;
  status: string;
  decision_deadline: string;
  decided_by: string | null;
  decision_reason: string | null;
  decided_at: string | null;
}

export async function getAdminDashboard(
  departmentId: string,
): Promise<AdminDashboard> {
  const response = await apiRequest<{
    data: AdminDashboard;
  }>(`/admin/departments/${encodeURIComponent(departmentId)}/dashboard`);

  return response.data;
}

export async function reassignPatient(
  queueEntryId: string,
  doctorId: string,
): Promise<ReassignmentResponse> {
  const response = await apiRequest<{
    data: ReassignmentResponse;
  }>("/admin/reassignments", {
    method: "POST",
    body: JSON.stringify({
      queue_entry_id: queueEntryId,
      doctor_id: doctorId,
    }),
  });

  return response.data;
}

export async function approvePromotion(
  promotionRequestId: string,
  decisionReason?: string,
): Promise<PromotionResponse> {
  const response = await apiRequest<{
    data: PromotionResponse;
  }>(`/promotions/${encodeURIComponent(promotionRequestId)}/approve`, {
    method: "POST",
    body: JSON.stringify({
      decision_reason: decisionReason ?? undefined,
    }),
  });

  return response.data;
}

export async function denyPromotion(
  promotionRequestId: string,
  decisionReason?: string,
): Promise<PromotionResponse> {
  const response = await apiRequest<{
    data: PromotionResponse;
  }>(`/promotions/${encodeURIComponent(promotionRequestId)}/deny`, {
    method: "POST",
    body: JSON.stringify({
      decision_reason: decisionReason ?? undefined,
    }),
  });

  return response.data;
}
