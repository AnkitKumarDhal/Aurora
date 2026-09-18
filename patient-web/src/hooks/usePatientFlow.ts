import { useState } from "react";
import { getConsentInformation, recordConsent } from "@/api/consent";
import { createSession } from "@/api/sessions";
import { identifyPatient } from "@/api/verification";

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

export type PatientVisitType = "FIRST_VISIT" | "RETURNING_VISIT" | null;

export function usePatientFlow() {
  const [currentScreen, setCurrentScreen] = useState<PatientScreen>("language");
  const [language, setLanguage] = useState<"en" | "hi">("en");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [identityType, setIdentityType] = useState<"abha" | "aadhaar" | null>(
    null,
  );
  const [identityIdentifier, setIdentityIdentifier] = useState<string | null>(
    null,
  );
  const [visitType, setVisitType] = useState<PatientVisitType>(null);
  const [isCreatingSession, setIsCreatingSession] = useState(false);
  const [sessionError, setSessionError] = useState<string | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationError, setVerificationError] = useState<string | null>(
    null,
  );
  const [consentVersion, setConsentVersion] = useState<string | null>(null);
  const [isRecordingConsent, setIsRecordingConsent] = useState(false);
  const [consentError, setConsentError] = useState<string | null>(null);

  function resetFlow() {
    setCurrentScreen("language");
    setLanguage("en");
    setSessionId(null);
    setIdentityType(null);
    setIdentityIdentifier(null);
    setVisitType(null);
    setConsentVersion(null);
    setSessionError(null);
    setVerificationError(null);
    setConsentError(null);
    setIsCreatingSession(false);
    setIsVerifying(false);
    setIsRecordingConsent(false);
  }

  function handleLanguageSelect(selectedLanguage: "en" | "hi") {
    setLanguage(selectedLanguage);
    setCurrentScreen("welcome");
  }

  async function handleStart() {
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
  }

  async function handleIdentityVerification(
    selectedIdentityType: "abha" | "aadhaar",
    identifier: string,
  ) {
    if (!sessionId || isVerifying) {
      return;
    }

    setVerificationError(null);
    setIsVerifying(true);

    try {
      const identification = await identifyPatient(
        sessionId,
        selectedIdentityType.toUpperCase(),
        identifier,
      );

      if (identification.status !== "VERIFIED") {
        throw new Error("Identity verification failed");
      }

      const consent = await getConsentInformation(sessionId);

      setIdentityType(selectedIdentityType);
      setIdentityIdentifier(identifier);
      setVisitType(identification.visit_type);
      setConsentVersion(consent.version);
      setCurrentScreen("consent");
    } catch (error) {
      setVerificationError(
        error instanceof Error ? error.message : "Identity verification failed",
      );
    } finally {
      setIsVerifying(false);
    }
  }

  async function handleConsentGrant() {
    if (
      !sessionId ||
      !consentVersion ||
      !identityType ||
      !identityIdentifier ||
      isRecordingConsent
    ) {
      return;
    }

    setConsentError(null);
    setIsRecordingConsent(true);

    try {
      const response = await recordConsent(
        sessionId,
        consentVersion,
        true,
        identityType.toUpperCase(),
        identityIdentifier,
      );

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
  }

  async function handleConsentDecline() {
    if (!sessionId || !consentVersion || isRecordingConsent) {
      return;
    }

    setConsentError(null);
    setIsRecordingConsent(true);

    try {
      const response = await recordConsent(
        sessionId,
        consentVersion,
        false,
        identityType?.toUpperCase() ?? "",
        identityIdentifier ?? "",
      );

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
  }

  return {
    currentScreen,
    language,
    sessionId,
    visitType,
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
