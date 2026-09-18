import { useCallback, useState } from "react";
import { createSession } from "@/api/sessions";
import { recordConsent, getConsentInformation } from "@/api/consent";
import { verifyPatient } from "@/api/verification";

export type PatientScreen =
  | "language"
  | "welcome"
  | "identity"
  | "consent"
  | "ai-mode"
  | "ai-voice"
  | "ai-text"
  | "upload"
  | "waiting";

export function usePatientFlow() {
  const [currentScreen, setCurrentScreen] = useState<PatientScreen>("language");
  const [language, setLanguage] = useState<"en" | "hi">("en");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isCreatingSession, setIsCreatingSession] = useState(false);
  const [sessionError, setSessionError] = useState<string | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationError, setVerificationError] = useState<string | null>(
    null,
  );
  const [consentVersion, setConsentVersion] = useState<string | null>(null);
  const [isRecordingConsent, setIsRecordingConsent] = useState(false);
  const [consentError, setConsentError] = useState<string | null>(null);

  const handleLanguageSelect = useCallback((selectedLanguage: "en" | "hi") => {
    setLanguage(selectedLanguage);
    setCurrentScreen("welcome");
  }, []);

  const handleStart = useCallback(async () => {
    setSessionError(null);
    setIsCreatingSession(true);

    try {
      const session = await createSession();
      setSessionId(session.session_id);
      setCurrentScreen("identity");
    } catch (error) {
      setSessionError(
        error instanceof Error ? error.message : "Unable to start your session",
      );
    } finally {
      setIsCreatingSession(false);
    }
  }, []);

  const handleIdentityVerification = useCallback(
    async (identityType: "abha" | "aadhaar", identifier: string) => {
      if (!sessionId || isVerifying) {
        return;
      }

      setVerificationError(null);
      setIsVerifying(true);

      try {
        const verification = await verifyPatient(
          sessionId,
          identityType.toUpperCase(),
          identifier,
        );

        if (verification.status !== "VERIFIED") {
          throw new Error("Identity verification failed");
        }

        const consent = await getConsentInformation(sessionId);
        setConsentVersion(consent.version);
        setCurrentScreen("consent");
      } catch (error) {
        setVerificationError(
          error instanceof Error
            ? error.message
            : "Identity verification failed",
        );
      } finally {
        setIsVerifying(false);
      }
    },
    [isVerifying, sessionId],
  );

  const handleConsentGrant = useCallback(async () => {
    if (!sessionId || !consentVersion || isRecordingConsent) {
      return;
    }

    setConsentError(null);
    setIsRecordingConsent(true);

    try {
      const response = await recordConsent(sessionId, consentVersion, true);

      if (response.consent_status !== "GRANTED") {
        throw new Error("Consent could not be recorded");
      }

      setCurrentScreen("ai-mode");
    } catch (error) {
      setConsentError(
        error instanceof Error ? error.message : "Unable to record consent",
      );
    } finally {
      setIsRecordingConsent(false);
    }
  }, [consentVersion, isRecordingConsent, sessionId]);

  const handleConsentDecline = useCallback(async () => {
    if (!sessionId || !consentVersion || isRecordingConsent) {
      return;
    }

    setConsentError(null);
    setIsRecordingConsent(true);

    try {
      const response = await recordConsent(sessionId, consentVersion, false);

      if (response.consent_status !== "DENIED") {
        throw new Error("Consent could not be recorded");
      }

      resetFlow();
    } catch (error) {
      setConsentError(
        error instanceof Error
          ? error.message
          : "Unable to record your response",
      );
    } finally {
      setIsRecordingConsent(false);
    }
  }, [consentVersion, isRecordingConsent, sessionId]);

  const resetFlow = useCallback(() => {
    setCurrentScreen("language");
    setLanguage("en");
    setSessionId(null);
    setConsentVersion(null);
    setSessionError(null);
    setVerificationError(null);
    setConsentError(null);
    setIsCreatingSession(false);
    setIsVerifying(false);
    setIsRecordingConsent(false);
  }, []);

  return {
    currentScreen,
    language,
    sessionId,
    isCreatingSession,
    sessionError,
    isVerifying,
    verificationError,
    isRecordingConsent,
    consentError,
    handleLanguageSelect,
    handleStart,
    handleIdentityVerification,
    handleConsentGrant,
    handleConsentDecline,
    resetFlow,
    setCurrentScreen,
  };
}
