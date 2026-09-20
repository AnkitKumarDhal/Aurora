import { create } from "zustand";
import type { ToastState, ToastType } from "@/types/admin";

interface AdminStore {
  selectedPatientId: string | null;
  isDrawerOpen: boolean;
  selectedDoctorFilter: string | null;
  toast: ToastState | null;
  showToast: (message: string, type?: ToastType) => void;
  openPatient: (patientId: string) => void;
  closeDrawer: () => void;
  setDoctorFilter: (doctorId: string) => void;
}

export const useAdminStore = create<AdminStore>((set) => ({
  selectedPatientId: null,
  isDrawerOpen: false,
  selectedDoctorFilter: null,
  toast: null,

  showToast: (message, type = "default") => {
    set({
      toast: {
        message,
        type,
      },
    });

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
    });
  },

  closeDrawer: () => {
    set({
      isDrawerOpen: false,
    });
  },

  setDoctorFilter: (doctorId) => {
    set((state) => ({
      selectedDoctorFilter:
        state.selectedDoctorFilter === doctorId ? null : doctorId,
    }));
  },
}));
