import { useCallback, useEffect, useState } from "react";
import { getAdminDashboard, type AdminDashboard } from "@/api/admin";
import type {
  DashboardDoctor,
  DashboardStats,
  Patient,
  DoctorStatus,
  PatientState,
} from "@/types/admin";

const DEPARTMENT_ID = "general-medicine";

interface AdminDashboardView {
  departmentId: string;
  stats: DashboardStats;
  doctors: DashboardDoctor[];
  patients: Patient[];
}

function toDoctorStatus(status: string): DoctorStatus {
  return status === "Available" ? "Available" : "Unavailable";
}

function toPatientState(status: string): PatientState {
  switch (status) {
    case "WAITING":
      return "WAITING";
    case "READY":
      return "READY";
    case "CALLED":
      return "CALLED";
    case "PROMOTION_PENDING":
      return "PROMOTION_PENDING";
    case "IN_CONSULTATION":
      return "IN_CONSULTATION";
    case "COMPLETED":
      return "COMPLETED";
    case "CANCELLED":
      return "CANCELLED";
    default:
      return "WAITING";
  }
}

function mapDashboard(dashboard: AdminDashboard): AdminDashboardView {
  return {
    departmentId: dashboard.department_id,

    stats: dashboard.stats,

    doctors: dashboard.doctors.map((doctor) => ({
      id: doctor.doctor_id,
      name: doctor.display_name,
      status: toDoctorStatus(doctor.status),
      assignedCount: doctor.assigned_count,
    })),

    patients: dashboard.patients.map((patient) => ({
      id: patient.patient_id,
      queueEntryId: patient.queue_entry_id,
      sessionId: patient.session_id,
      patientId: patient.patient_id,
      name: patient.display_name,
      age: patient.age,
      urgencyLevel: patient.urgency_level,
      priorityScore: patient.priority_score,
      state: toPatientState(patient.queue_status),
      doctorId: patient.doctor_id,
      doctor: patient.doctor_name,
      complaint: patient.chief_complaint,
      queuedAt: patient.queued_at,
      waitingTimeSeconds: patient.waiting_time_seconds,
    })),
  };
}

export function useAdminDashboard(enabled: boolean) {
  const [dashboard, setDashboard] = useState<AdminDashboardView | null>(null);

  const [isLoading, setIsLoading] = useState(true);

  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!enabled) {
      return;
    }

    try {
      setError(null);

      const response = await getAdminDashboard(DEPARTMENT_ID);

      setDashboard(mapDashboard(response));
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Unable to load admin dashboard.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [enabled]);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    const initialLoad = window.setTimeout(() => {
      void load();
    }, 0);

    const refreshTimer = window.setInterval(() => {
      void load();
    }, 5000);

    return () => {
      window.clearTimeout(initialLoad);

      window.clearInterval(refreshTimer);
    };
  }, [enabled, load]);

  return {
    dashboard,
    isLoading,
    error,
    reload: load,
  };
}
