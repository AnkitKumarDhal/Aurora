import { useState } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/auth/useAuth";

export default function LoginPage() {
  const { isAuthenticated, isLoading, login } = useAuth();
  const location = useLocation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (isLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background">
        <p className="text-sm text-text-secondary">Loading...</p>
      </main>
    );
  }

  if (isAuthenticated) {
    const destination =
      typeof location.state?.from === "string" ? location.state.from : "/queue";

    return <Navigate to={destination} replace />;
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background p-6">
      <section className="w-full max-w-[380px] rounded-[20px] border border-border bg-surface px-8 pb-7 pt-9 shadow-[0_24px_48px_-24px_rgba(58,46,92,0.28)]">
        <div className="flex items-center gap-2.5">
          <span className="aurora-mark aurora-mark-lg" />
          <span className="font-display text-[21px] font-medium text-primary-dark">
            Aurora
          </span>
        </div>

        <div className="mt-7">
          <h1 className="font-display text-[23px] font-semibold leading-tight text-text-primary">
            Doctor sign in
          </h1>

          <p className="mt-1.5 text-[12px] leading-5 text-text-secondary">
            General Medicine · OPD clinical workspace
          </p>
        </div>

        <form
          className="mt-6 space-y-4"
          onSubmit={async (event) => {
            event.preventDefault();
            setError("");
            setIsSubmitting(true);

            try {
              await login({ username, password });
            } catch (error) {
              setError(
                error instanceof Error ? error.message : "Unable to sign in",
              );
            } finally {
              setIsSubmitting(false);
            }
          }}
        >
          <div className="space-y-1.5">
            <label
              className="text-[11px] font-semibold text-text-secondary"
              htmlFor="username"
            >
              Username
            </label>

            <input
              id="username"
              className="h-9 w-full rounded-md border border-border bg-surface-alt px-3 text-xs text-text-primary outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20"
              autoComplete="username"
              disabled={isSubmitting}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="doctor1"
              required
              type="text"
              value={username}
            />
          </div>

          <div className="space-y-1.5">
            <label
              className="text-[11px] font-semibold text-text-secondary"
              htmlFor="password"
            >
              Password
            </label>

            <input
              id="password"
              className="h-9 w-full rounded-md border border-border bg-surface-alt px-3 text-xs text-text-primary outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20"
              autoComplete="current-password"
              disabled={isSubmitting}
              onChange={(event) => setPassword(event.target.value)}
              required
              type="password"
              value={password}
            />
          </div>

          {error && (
            <p
              className="rounded-md bg-accent-tint px-3 py-2 text-[11px] leading-4 text-accent-dark"
              role="alert"
            >
              {error}
            </p>
          )}

          <Button
            className="h-9 w-full rounded-md bg-primary-dark text-xs font-semibold text-white shadow-sm hover:bg-primary-dark/90"
            disabled={isSubmitting}
            type="submit"
          >
            {isSubmitting ? "Signing in..." : "Sign in"}
          </Button>
        </form>

        <p className="mt-4 text-center text-[10px] leading-4 text-text-secondary">
          Calls{" "}
          <span className="rounded bg-primary-tint px-1 py-0.5 font-medium">
            POST /api/v1/auth/login
          </span>{" "}
          · stores{" "}
          <span className="rounded bg-primary-tint px-1 py-0.5 font-medium">
            access_token
          </span>{" "}
          as a bearer token
        </p>
      </section>
    </main>
  );
}
