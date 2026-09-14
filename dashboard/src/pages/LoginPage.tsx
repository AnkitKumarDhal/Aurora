import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronLeft } from "lucide-react";
import { useAuth, homeRouteForRole } from "@/lib/auth";
import { useOnboarding } from "@/lib/onboarding";
import { ApiError } from "@/lib/api";

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const { role } = useOnboarding();
  const [loginId, setLoginId] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const heading =
    role === "doctor"
      ? "Doctor sign in"
      : role === "patient"
        ? "Patient sign in"
        : "Sign in";

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { role: grantedRole } = await login(loginId.trim(), password);
      navigate(homeRouteForRole(grantedRole), { replace: true });
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Something went wrong. Try again.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col items-center px-4 py-6">
      <div className="w-full max-w-sm">
        <button
          onClick={() => navigate("/onboarding/role")}
          className="size-10 rounded-full bg-muted text-primary flex items-center justify-center mb-6"
          aria-label="Back"
        >
          <ChevronLeft className="size-5" />
        </button>

        <h1 className="text-2xl font-extrabold text-primary mb-1">{heading}</h1>
        <p className="text-muted-foreground mb-6">
          Enter your Login ID and password
        </p>

        {error && (
          <div className="mb-4 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-xl px-3 py-2">
            {error}
          </div>
        )}

        <form
          onSubmit={handleLogin}
          className="bg-card border border-border rounded-2xl p-5"
        >
          <label className="block text-sm font-bold text-foreground mb-1">
            Login ID
          </label>
          <input
            className="w-full border border-border rounded-xl px-3 py-2.5 mb-4 bg-background"
            placeholder="e.g. a1b2c3d4"
            value={loginId}
            onChange={(e) => setLoginId(e.target.value)}
            autoComplete="username"
            required
          />

          <label className="block text-sm font-bold text-foreground mb-1">
            Password
          </label>
          <input
            className="w-full border border-border rounded-xl px-3 py-2.5 mb-5 bg-background"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary text-primary-foreground rounded-xl py-3 font-bold disabled:opacity-50"
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <p className="text-sm text-muted-foreground text-center mt-4">
          New here?{" "}
          <button
            type="button"
            className="text-primary font-bold hover:underline"
            onClick={() => navigate("/register")}
          >
            Create an account
          </button>
        </p>
      </div>
    </div>
  );
}
