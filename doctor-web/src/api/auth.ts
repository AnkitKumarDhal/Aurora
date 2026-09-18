import { apiRequest } from "@/api/client";
import type { CurrentUser, LoginRequest, LoginResponse } from "@/types/api";

export async function login(credentials: LoginRequest): Promise<LoginResponse> {
  const response = await apiRequest<{ data: LoginResponse }>("/auth/login", {
    method: "POST",
    body: JSON.stringify(credentials),
  });

  return response.data;
}

export async function getCurrentUser(): Promise<CurrentUser> {
  const response = await apiRequest<{ data: CurrentUser }>("/auth/me");

  return response.data;
}
