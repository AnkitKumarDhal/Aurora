import { useNavigate } from "react-router-dom";
import { OnboardingShell } from "@/components/OnboardingShell";
import { useOnboarding } from "@/lib/onboarding";

const LANGUAGES = [
  { code: "en", glyph: "A", label: "English" },
  { code: "hi", glyph: "अ", label: "हिन्दी" },
  { code: "or", glyph: "ଅ", label: "ଓଡ଼ିଆ" },
  { code: "bn", glyph: "অ", label: "বাংলা" },
];

export default function LanguagePage() {
  const navigate = useNavigate();
  const { language, setLanguage } = useOnboarding();

  return (
    <OnboardingShell
      step={2}
      onBack={() => navigate(-1)}
      onNext={() => navigate("/onboarding/role")}
    >
      <h1 className="text-2xl font-extrabold text-primary mb-1">
        Choose your language
      </h1>
      <p className="text-muted-foreground mb-6">Tap a box, then the arrow</p>

      <div className="grid grid-cols-2 gap-3">
        {LANGUAGES.map((l) => {
          const selected = language === l.code;
          return (
            <button
              key={l.code}
              onClick={() => setLanguage(l.code)}
              className={`rounded-2xl border-2 py-6 text-center transition-colors ${
                selected ? "bg-muted border-accent" : "bg-card border-border"
              }`}
            >
              <div className="text-2xl font-extrabold text-primary mb-1">
                {l.glyph}
              </div>
              <div className="text-sm text-muted-foreground">{l.label}</div>
            </button>
          );
        })}
      </div>
    </OnboardingShell>
  );
}
