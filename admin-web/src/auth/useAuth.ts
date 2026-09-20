import { login, logout, useAdminAuth } from "./store";

export function useAuth() {
  const snapshot = useAdminAuth();

  return {
    user: snapshot.user,
    isLoading: snapshot.status === "loading",
    isAuthenticated: snapshot.status === "authenticated",
    login,
    logout,
  };
}
