import { createContext, useContext, useState, type ReactNode } from "react";
import * as api from "@/lib/api";
import type { Role } from "@/lib/api";

const STORAGE_KEY = "aurora_auth";

type AuthState = {
  token: string | null;
  role: Role | null;
  loginId: string | null;
};

type AuthContextValue = AuthState & {
  login: (loginId: string, password: string) => Promise<AuthState>;
  register: (payload: api.RegisterPayload) => Promise<AuthState>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function loadState(): AuthState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { token: null, role: null, loginId: null };
    return JSON.parse(raw);
  } catch {
    return { token: null, role: null, loginId: null };
  }
}

function saveState(state: AuthState) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(loadState);

  const applyAuthResponse = (res: api.AuthResponse): AuthState => {
    const next: AuthState = {
      token: res.access_token,
      role: res.role,
      loginId: res.login_id,
    };
    saveState(next);
    setState(next);
    return next;
  };

  const login = async (loginId: string, password: string) => {
    const res = await api.login({ login_id: loginId, password });
    return applyAuthResponse(res);
  };

  const register = async (payload: api.RegisterPayload) => {
    const res = await api.register(payload);
    return applyAuthResponse(res);
  };

  const logout = () => {
    localStorage.removeItem(STORAGE_KEY);
    setState({ token: null, role: null, loginId: null });
  };

  return (
    <AuthContext.Provider value={{ ...state, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export function homeRouteForRole(role: Role | null) {
  if (role === "doctor") return "/queue";
  if (role === "patient") return "/my-summary";
  return "/login";
}
