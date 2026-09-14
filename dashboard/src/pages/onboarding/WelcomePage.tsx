import { useNavigate } from "react-router-dom";
import { OnboardingShell } from "@/components/OnboardingShell";

export default function WelcomePage() {
  const navigate = useNavigate();

  return (
    <OnboardingShell step={0} onNext={() => navigate("/onboarding/location")}>
      <div className="h-full flex flex-col items-center justify-center text-center pt-24">
        <div className="size-24 rounded-full bg-muted flex items-center justify-center mb-6">
          <span className="text-4xl font-extrabold text-primary">
            A<span className="text-accent">·</span>
          </span>
        </div>
        <h1 className="text-3xl font-extrabold text-primary mb-2">Aurora</h1>
        <p className="text-muted-foreground">Tap the glowing arrow to begin</p>
      </div>
    </OnboardingShell>
  );
}
