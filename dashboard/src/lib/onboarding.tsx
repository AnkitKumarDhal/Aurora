import { createContext, useContext, useState, type ReactNode } from "react";
import type { Role } from "./api";

type OnboardingState = {
  language: string;
  location: string | null;
  role: Role | null;
};

type OnboardingContextValue = OnboardingState & {
  setLanguage: (lang: string) => void;
  setLocation: (loc: string) => void;
  setRole: (role: Role) => void;
};

const OnboardingContext = createContext<OnboardingContextValue | null>(null);

export function OnboardingProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState("en");
  const [location, setLocation] = useState<string | null>(null);
  const [role, setRole] = useState<Role | null>(null);

  return (
    <OnboardingContext.Provider
      value={{ language, location, role, setLanguage, setLocation, setRole }}
    >
      {children}
    </OnboardingContext.Provider>
  );
}

export function useOnboarding() {
  const ctx = useContext(OnboardingContext);
  if (!ctx)
    throw new Error("useOnboarding must be used within OnboardingProvider");
  return ctx;
}
