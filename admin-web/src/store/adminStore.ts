import { create } from "zustand";
import { initialDoctors, initialPatients } from "@/data/mockData";
import type { PromotionState, ToastState, ToastType } from "@/types/admin";

interface AdminStore {
  patients: typeof initialPatients;
  selectedPatientId: string | null;
  isDrawerOpen: boolean;
  isReassigning: boolean;
  selectedDoctorFilter: string | null;
  promotionState: PromotionState;
  toast: ToastState | null;
  showToast: (message: string, type?: ToastType) => void;
  openPatient: (patientId: string) => void;
  closeDrawer: () => void;
  openReassign: () => void;
  cancelReassign: () => void;
  confirmReassign: (doctorName: string) => void;
  setDoctorFilter: (doctorId: string) => void;
  resolvePromotion: (
    state: Exclude<PromotionState, "active" | "empty">,
  ) => void;
  clearPromotion: () => void;
}

export const useAdminStore = create<AdminStore>((set, get) => ({
  patients: initialPatients,
  selectedPatientId: null,
  isDrawerOpen: false,
  isReassigning: false,
  selectedDoctorFilter: null,
  promotionState: "active",
  toast: null,

  showToast: (message, type = "default") => {
    set({ toast: { message, type } });

    window.setTimeout(() => {
      set((state) => ({
        toast: state.toast?.message === message ? null : state.toast,
      }));
    }, 2500);
  },

  openPatient: (patientId) => {
    set({
      selectedPatientId: patientId,
      isDrawerOpen: true,
      isReassigning: false,
    });
  },

  closeDrawer: () => {
    set({
      isDrawerOpen: false,
      isReassigning: false,
    });
  },

  openReassign: () => {
    if (!get().selectedPatientId) {
      return;
    }

    set({ isReassigning: true });
  },

  cancelReassign: () => {
    set({ isReassigning: false });
  },

  confirmReassign: (doctorName) => {
    const patientId = get().selectedPatientId;

    if (!patientId || !doctorName) {
      return;
    }

    set((state) => ({
      patients: state.patients.map((patient) =>
        patient.id === patientId
          ? {
              ...patient,
              doctor: doctorName,
              stale: false,
            }
          : patient,
      ),
      isReassigning: false,
    }));

    get().showToast(`Reassigned ${patientId} to ${doctorName}`, "success");
  },

  setDoctorFilter: (doctorId) => {
    set((state) => ({
      selectedDoctorFilter:
        state.selectedDoctorFilter === doctorId ? null : doctorId,
    }));

    const activeFilter = get().selectedDoctorFilter;

    if (activeFilter) {
      const doctor = initialDoctors.find((item) => item.id === activeFilter);

      if (doctor) {
        get().showToast(`Filtered to ${doctor.name}'s patients`);
      }
    } else {
      get().showToast("Filter cleared");
    }
  },

  resolvePromotion: (state) => {
    set({ promotionState: state });

    if (state === "accepted") {
      get().showToast("Promotion accepted for A102", "success");
    }

    if (state === "denied") {
      get().showToast("Promotion denied for A102", "deny");
    }

    if (state === "auto") {
      get().showToast("A102 auto-promoted after timeout", "auto");
    }
  },

  clearPromotion: () => {
    set({ promotionState: "empty" });
  },
}));
