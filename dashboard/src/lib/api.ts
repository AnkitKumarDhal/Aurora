const API_BASE = import.meta.env.VITE_API_URL as string;

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      message = body?.error?.message || body?.detail || message;
    } catch {
      throw new ApiError(res.status, message);
    }
    throw new ApiError(res.status, message);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export type Role = "patient" | "doctor";

export interface AuthResponse {
  access_token: string;
  token_type: string;
  role: Role;
  login_id: string;
}

export interface RegisterPayload {
  name: string;
  role: Role;
  password: string;
  age?: number;
  gender?: string;
  phone?: string;
  specialization?: string;
}

export function login(payload: { login_id: string; password: string }) {
  return apiFetch<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function register(payload: RegisterPayload) {
  return apiFetch<AuthResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export { apiFetch, API_BASE };
