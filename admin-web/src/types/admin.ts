export type PatientState = "Waiting" | "In Consultation";

export type DoctorStatus = "Available" | "Consulting" | "Unavailable";

export type PromotionState =
  | "active"
  | "accepted"
  | "denied"
  | "auto"
  | "empty";

export type ToastType = "success" | "deny" | "auto" | "default";

export interface Patient {
  id: string;
  name: string;
  ageSex: string;
  mrn: string;
  priority: "High Priority" | "Normal";
  state: PatientState;
  wait: string;
  waitMinutes: number | null;
  doctor: string;
  complaint: string;
  cardComplaint: string;
  triage: string;
  severity: string;
  stale?: boolean;
}

export interface Doctor {
  id: string;
  name: string;
  status: DoctorStatus;
  assignedCount: number;
}

export interface ToastState {
  message: string;
  type: ToastType;
}
