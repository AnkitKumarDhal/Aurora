import { useSyncExternalStore } from "react";
import { getCurrentUser, login as loginRequest } from "@/api/auth";
import { clearAccessToken, getAccessToken, setAccessToken } from "./auth";

export type AuthStatus = "loading" | "authenticated" | "anonymous";

interface AuthSnapshot {
  status: AuthStatus;
  user: Awaited<ReturnType<typeof getCurrentUser>> | null;
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

    if (user.role !== "ADMIN") {
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

export async function login(username: string, password: string): Promise<void> {
  const response = await loginRequest(username, password);

  setAccessToken(response.access_token);

  const user = await getCurrentUser();

  if (user.role !== "ADMIN") {
    clearAccessToken();

    setSnapshot({
      status: "anonymous",
      user: null,
    });

    throw new Error("This application is restricted to administrators.");
  }

  setSnapshot({
    status: "authenticated",
    user,
  });
}

export function logout(): void {
  clearAccessToken();

  setSnapshot({
    status: "anonymous",
    user: null,
  });
}

export function useAdminAuth() {
  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}
