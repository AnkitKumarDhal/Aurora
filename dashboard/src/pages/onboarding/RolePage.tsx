import { useNavigate } from "react-router-dom";
import { User, Stethoscope } from "lucide-react";
import { OnboardingShell } from "@/components/OnboardingShell";
import { useOnboarding } from "@/lib/onboarding";
import type { Role } from "@/lib/api";

export default function RolePage() {
  const navigate = useNavigate();
  const { setRole } = useOnboarding();

  const choose = (role: Role) => {
    setRole(role);
    navigate("/login");
  };

  return (
    <OnboardingShell step={3} onBack={() => navigate(-1)}>
      <h1 className="text-2xl font-extrabold text-primary mb-1">
        Who are you?
      </h1>
      <p className="text-muted-foreground mb-6">Tap your picture</p>

      <div className="grid grid-cols-2 gap-3">
        <button
          onClick={() => choose("patient")}
          className="bg-card border border-border rounded-2xl py-8 flex flex-col items-center gap-3"
        >
          <span className="size-12 rounded-xl bg-muted flex items-center justify-center">
            <User className="size-6 text-primary" />
          </span>
          <span className="font-bold text-foreground">Patient</span>
        </button>
        <button
          onClick={() => choose("doctor")}
          className="bg-card border border-border rounded-2xl py-8 flex flex-col items-center gap-3"
        >
          <span className="size-12 rounded-xl bg-muted flex items-center justify-center">
            <Stethoscope className="size-6 text-primary" />
          </span>
          <span className="font-bold text-foreground">Doctor</span>
        </button>
      </div>
    </OnboardingShell>
  );
}
