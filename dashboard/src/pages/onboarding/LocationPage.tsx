import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { MapPin, Clock } from "lucide-react";
import { OnboardingShell } from "@/components/OnboardingShell";
import { useOnboarding } from "@/lib/onboarding";

const MOCK_LOCATION = "Bhubaneswar, Odisha";

export default function LocationPage() {
  const navigate = useNavigate();
  const { setLocation } = useOnboarding();
  const [detecting, setDetecting] = useState(true);

  useEffect(() => {
    const t = setTimeout(() => setDetecting(false), 900);
    return () => clearTimeout(t);
  }, []);

  const handleNext = () => {
    setLocation(MOCK_LOCATION);
    navigate("/onboarding/language");
  };

  return (
    <OnboardingShell step={1} onBack={() => navigate(-1)} onNext={handleNext}>
      <h1 className="text-2xl font-extrabold text-primary mb-1">
        Where are you?
      </h1>
      <p className="text-muted-foreground mb-8">
        This helps us find your nearest clinic
      </p>

      <MapPin className="size-12 text-primary mb-6" fill="currentColor" />

      <div className="bg-card border border-border rounded-2xl p-4 flex items-center gap-3">
        <div className="size-10 rounded-xl bg-muted flex items-center justify-center shrink-0">
          <Clock className="size-5 text-primary" />
        </div>
        <div>
          <p className="font-bold text-foreground">
            {detecting ? "Detecting automatically…" : MOCK_LOCATION}
          </p>
          <p className="text-sm text-muted-foreground">Tap arrow to confirm</p>
        </div>
      </div>
    </OnboardingShell>
  );
}
