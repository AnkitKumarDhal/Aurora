import { apiRequest } from "@/api/client";
import type { CurrentUser, LoginRequest, LoginResponse } from "@/types/api";

export async function login(credentials: LoginRequest): Promise<LoginResponse> {
  return apiRequest<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(credentials),
  });
}

export async function getCurrentUser(): Promise<CurrentUser> {
  return apiRequest<{ data: CurrentUser }>("/auth/me").then(
    (response) => response.data,
  );
}
