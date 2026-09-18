import { useSyncExternalStore } from "react";
import { getSnapshot, login, logout, subscribe } from "@/auth/store";

export function useAuth() {
  const snapshot = useSyncExternalStore(subscribe, getSnapshot, getSnapshot);

  return {
    user: snapshot.user,
    isLoading: snapshot.status === "loading",
    isAuthenticated: snapshot.status === "authenticated",
    login,
    logout,
  };
}
