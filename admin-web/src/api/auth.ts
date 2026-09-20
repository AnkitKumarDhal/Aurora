import { apiRequest } from "./client";

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface CurrentUser {
  user_id: string;
  username: string;
  role: "ADMIN" | "DOCTOR" | "PATIENT";
  actor_id: string;
}

export async function login(
  username: string,
  password: string,
): Promise<LoginResponse> {
  const response = await apiRequest<{
    data: LoginResponse;
  }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({
      username,
      password,
    }),
  });

  return response.data;
}

export async function getCurrentUser(): Promise<CurrentUser> {
  const response = await apiRequest<{
    data: CurrentUser;
  }>("/auth/me");

  return response.data;
}
