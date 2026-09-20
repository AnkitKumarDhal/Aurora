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

export interface AdminDashboard {
  department_id: string;
  stats: AdminDashboardStats;
  doctors: AdminDashboardDoctor[];
  patients: AdminDashboardPatient[];
}

export async function getAdminDashboard(
  departmentId: string,
): Promise<AdminDashboard> {
  const response = await apiRequest<{ data: AdminDashboard }>(
    `/admin/departments/${encodeURIComponent(departmentId)}/dashboard`,
  );

  return response.data;
}
