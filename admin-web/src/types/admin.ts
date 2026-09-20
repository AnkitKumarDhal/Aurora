export type PatientState =
  | "WAITING"
  | "CALLED"
  | "PROMOTION_PENDING"
  | "IN_CONSULTATION";

export type DoctorStatus = "Available" | "Unavailable";

export interface Patient {
  id: string;
  queueEntryId: string;
  sessionId: string;
  patientId: string;
  name: string;
  age: number | null;
  urgencyLevel: number | null;
  priorityScore: number | null;
  state: PatientState;
  doctorId: string | null;
  doctor: string | null;
  complaint: string | null;
  queuedAt: string | null;
  waitingTimeSeconds: number | null;
}

export interface DashboardDoctor {
  id: string;
  name: string;
  status: DoctorStatus;
  assignedCount: number;
}

export interface DashboardStats {
  patients: number;
  waiting: number;
  in_consultation: number;
  doctors: number;
}

export type PromotionState =
  | "active"
  | "accepted"
  | "denied"
  | "auto"
  | "empty";

export type ToastType = "success" | "deny" | "auto" | "default";

export interface ToastState {
  message: string;
  type: ToastType;
}
