import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronLeft } from "lucide-react";
import { useAuth, homeRouteForRole } from "@/lib/auth";
import { useOnboarding } from "@/lib/onboarding";
import { ApiError, type Role } from "@/lib/api";

export default function RegisterPage() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const { role: onboardingRole } = useOnboarding();

  const [role, setRoleState] = useState<Role>(onboardingRole ?? "patient");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [age, setAge] = useState("");
  const [gender, setGender] = useState("");
  const [phone, setPhone] = useState("");
  const [specialization, setSpecialization] = useState("");

  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [issued, setIssued] = useState<{ loginId: string; role: Role } | null>(
    null,
  );

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const result = await register({
        name: name.trim(),
        role,
        password,
        ...(role === "patient"
          ? {
              age: age ? Number(age) : undefined,
              gender: gender || undefined,
              phone: phone || undefined,
            }
          : { specialization: specialization || undefined }),
      });
      setIssued({ loginId: result.loginId!, role: result.role! });
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

  if (issued) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center px-4">
        <div className="w-full max-w-sm bg-card border border-border rounded-2xl p-6 text-center">
          <h1 className="text-xl font-extrabold text-primary mb-2">
            Account created
          </h1>
          <p className="text-sm text-muted-foreground mb-4">
            Save this Login ID — you'll need it every time you sign in. It won't
            be shown again.
          </p>
          <div className="text-2xl font-mono font-extrabold tracking-widest bg-muted text-primary rounded-xl py-3 mb-6">
            {issued.loginId}
          </div>
          <button
            className="w-full bg-primary text-primary-foreground rounded-xl py-3 font-bold"
            onClick={() =>
              navigate(homeRouteForRole(issued.role), { replace: true })
            }
          >
            Continue
          </button>
        </div>
      </div>
    );
  }

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

        <h1 className="text-2xl font-extrabold text-primary mb-6">
          Create account
        </h1>

        {error && (
          <div className="mb-4 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-xl px-3 py-2">
            {error}
          </div>
        )}

        <form
          onSubmit={handleSubmit}
          className="bg-card border border-border rounded-2xl p-5"
        >
          <label className="block text-sm font-bold text-foreground mb-1">
            I am a
          </label>
          <div className="flex gap-2 mb-4">
            {(["patient", "doctor"] as const).map((r) => (
              <button
                key={r}
                type="button"
                onClick={() => setRoleState(r)}
                className={`flex-1 border-2 rounded-xl py-2 text-sm font-bold capitalize ${
                  role === r
                    ? "bg-muted border-accent text-primary"
                    : "bg-background border-border text-muted-foreground"
                }`}
              >
                {r}
              </button>
            ))}
          </div>

          <label className="block text-sm font-bold text-foreground mb-1">
            Full name
          </label>
          <input
            className="w-full border border-border rounded-xl px-3 py-2.5 mb-4 bg-background"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />

          {role === "patient" ? (
            <>
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div>
                  <label className="block text-sm font-bold text-foreground mb-1">
                    Age
                  </label>
                  <input
                    className="w-full border border-border rounded-xl px-3 py-2.5 bg-background"
                    type="number"
                    min={0}
                    value={age}
                    onChange={(e) => setAge(e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-foreground mb-1">
                    Gender
                  </label>
                  <select
                    className="w-full border border-border rounded-xl px-3 py-2.5 bg-background"
                    value={gender}
                    onChange={(e) => setGender(e.target.value)}
                  >
                    <option value="">Select</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>
              <label className="block text-sm font-bold text-foreground mb-1">
                Phone
              </label>
              <input
                className="w-full border border-border rounded-xl px-3 py-2.5 mb-4 bg-background"
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
              />
            </>
          ) : (
            <>
              <label className="block text-sm font-bold text-foreground mb-1">
                Specialization
              </label>
              <input
                className="w-full border border-border rounded-xl px-3 py-2.5 mb-4 bg-background"
                value={specialization}
                onChange={(e) => setSpecialization(e.target.value)}
                placeholder="e.g. General Medicine"
              />
            </>
          )}

          <label className="block text-sm font-bold text-foreground mb-1">
            Password
          </label>
          <input
            className="w-full border border-border rounded-xl px-3 py-2.5 mb-5 bg-background"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
            required
          />

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary text-primary-foreground rounded-xl py-3 font-bold disabled:opacity-50"
          >
            {loading ? "Creating account…" : "Create account"}
          </button>
        </form>

        <p className="text-sm text-muted-foreground text-center mt-4">
          Already have an account?{" "}
          <button
            type="button"
            className="text-primary font-bold hover:underline"
            onClick={() => navigate("/login")}
          >
            Sign in
          </button>
        </p>
      </div>
    </div>
  );
}
