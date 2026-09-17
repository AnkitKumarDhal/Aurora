import type { ApiError } from "@/types/api";
import { getAccessToken } from "@/auth/auth";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export class ApiRequestError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiRequestError";
    this.status = status;
    this.detail = detail;
  }
}

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiRequestError) {
    return error.detail;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return fallback;
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getAccessToken();
  const headers = new Headers(options.headers);

  headers.set("Accept", "application/json");

  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let detail = "";

    try {
      const error = (await response.json()) as ApiError;

      if (error.detail) {
        detail = error.detail;
      }
    } catch {
      detail = "";
    }

    if (!detail) {
      switch (response.status) {
        case 400:
          detail = "The request could not be completed.";
          break;
        case 401:
          detail = "Your session has expired. Please sign in again.";
          break;
        case 403:
          detail = "You do not have permission to perform this action.";
          break;
        case 404:
          detail = "The requested resource could not be found.";
          break;
        case 409:
          detail = "The request conflicts with the current case state.";
          break;
        case 500:
          detail = "The server encountered an unexpected error.";
          break;
        case 502:
        case 503:
        case 504:
          detail = "Aurora is temporarily unavailable. Please try again.";
          break;
        default:
          detail = `The request could not be completed (HTTP ${response.status}).`;
      }
    }

    throw new ApiRequestError(response.status, detail);
  }
  return response.json() as Promise<T>;
}
