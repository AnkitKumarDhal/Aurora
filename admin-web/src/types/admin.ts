export type PatientState =
  | "WAITING"
  | "READY"
  | "CALLED"
  | "PROMOTION_PENDING"
  | "IN_CONSULTATION"
  | "COMPLETED"
  | "CANCELLED";

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

export interface AdminPromotion {
  promotionRequestId: string;
  queueEntryId: string;
  patientId: string;
  patientName: string;
  currentDoctorId: string | null;
  currentDoctorName: string | null;
  targetDoctorId: string;
  targetDoctorName: string;
  reason: string;
  status:
    | "PENDING"
    | "APPROVED"
    | "AUTO_APPROVED"
    | "DENIED"
    | "CANCELLED"
    | "EXPIRED";
  decisionDeadline: string;
}

export type ToastType = "success" | "deny" | "auto" | "default";

export interface ToastState {
  message: string;
  type: ToastType;
}
