import { getCurrentUser, login as loginRequest } from "@/api/auth";
import { clearAccessToken, getAccessToken, setAccessToken } from "@/auth/auth";
import type { CurrentUser, LoginRequest } from "@/types/api";

export type AuthStatus = "loading" | "authenticated" | "anonymous";

export interface AuthSnapshot {
  status: AuthStatus;
  user: CurrentUser | null;
}

let snapshot: AuthSnapshot = {
  status: getAccessToken() ? "loading" : "anonymous",
  user: null,
};

const listeners = new Set<() => void>();

function emit(): void {
  for (const listener of listeners) {
    listener();
  }
}

function setSnapshot(nextSnapshot: AuthSnapshot): void {
  snapshot = nextSnapshot;
  emit();
}

export function subscribe(listener: () => void): () => void {
  listeners.add(listener);

  return () => {
    listeners.delete(listener);
  };
}

export function getSnapshot(): AuthSnapshot {
  return snapshot;
}

export async function initializeAuth(): Promise<void> {
  if (!getAccessToken()) {
    setSnapshot({
      status: "anonymous",
      user: null,
    });
    return;
  }

  try {
    const user = await getCurrentUser();

    if (user.role !== "DOCTOR") {
      clearAccessToken();

      setSnapshot({
        status: "anonymous",
        user: null,
      });

      return;
    }

    setSnapshot({
      status: "authenticated",
      user,
    });
  } catch {
    clearAccessToken();

    setSnapshot({
      status: "anonymous",
      user: null,
    });
  }
}

export async function login(credentials: LoginRequest): Promise<void> {
  const response = await loginRequest(credentials);

  setAccessToken(response.access_token);

  try {
    const user = await getCurrentUser();

    if (user.role !== "DOCTOR") {
      clearAccessToken();
      throw new Error("This application is restricted to doctors");
    }

    setSnapshot({
      status: "authenticated",
      user,
    });
  } catch (error) {
    clearAccessToken();

    setSnapshot({
      status: "anonymous",
      user: null,
    });

    throw error;
  }
}

export function logout(): void {
  clearAccessToken();

  setSnapshot({
    status: "anonymous",
    user: null,
  });
}
