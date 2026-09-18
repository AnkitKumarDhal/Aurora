import { useEffect, useRef, useState } from "react";
import { getConsentInformation, recordConsent } from "@/api/consent";
import { createSession, getSession } from "@/api/sessions";
import { requestIdentityOtp, verifyPatientOtp } from "@/api/verification";

const SESSION_STORAGE_KEY = "aurora.patient.session_id";

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

function readStoredSessionId(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    return window.sessionStorage.getItem(SESSION_STORAGE_KEY);
  } catch {
    return null;
  }
}

function storeSessionId(sessionId: string): void {
  try {
    window.sessionStorage.setItem(SESSION_STORAGE_KEY, sessionId);
  } catch {
    return;
  }
}

function clearStoredSessionId(): void {
  try {
    window.sessionStorage.removeItem(SESSION_STORAGE_KEY);
  } catch {
    return;
  }
}

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
  const [otpChallengeId, setOtpChallengeId] = useState<string | null>(null);
  const [otpDemoCode, setOtpDemoCode] = useState<string | null>(null);
  const [isCreatingSession, setIsCreatingSession] = useState(false);
  const [sessionError, setSessionError] = useState<string | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationError, setVerificationError] = useState<string | null>(
    null,
  );
  const [consentVersion, setConsentVersion] = useState<string | null>(null);
  const [consentText, setConsentText] = useState<string | null>(null);
  const [isRecordingConsent, setIsRecordingConsent] = useState(false);
  const [consentError, setConsentError] = useState<string | null>(null);
  const [isRestoringSession, setIsRestoringSession] = useState(false);
  const [isNavigatingBack, setIsNavigatingBack] = useState(false);
  const consentSubmissionLock = useRef(false);

  const resetFlow = () => {
    clearStoredSessionId();
    consentSubmissionLock.current = false;
    setCurrentScreen("language");
    setLanguage("en");
    setSessionId(null);
    setIdentityType(null);
    setIdentityIdentifier(null);
    setVisitType(null);
    setOtpChallengeId(null);
    setOtpDemoCode(null);
    setConsentVersion(null);
    setConsentText(null);
    setSessionError(null);
    setVerificationError(null);
    setConsentError(null);
    setIsCreatingSession(false);
    setIsVerifying(false);
    setIsRecordingConsent(false);
    setIsNavigatingBack(false);
  };

  useEffect(() => {
    const storedSessionId = readStoredSessionId();

    if (!storedSessionId) {
      return;
    }

    let active = true;

    const restoreSession = async () => {
      setIsRestoringSession(true);
      setSessionError(null);

      try {
        const session = await getSession(storedSessionId);

        if (!active) {
          return;
        }

        setSessionId(session.session_id);

        if (session.status === "CREATED" || session.status === "IDENTIFYING") {
          setCurrentScreen("identity");
          return;
        }

        if (
          session.status === "CONSENTED" ||
          session.status === "HISTORY_IN_PROGRESS"
        ) {
          setCurrentScreen("ai-mode");
          return;
        }

        if (session.status === "DOCUMENT_PROCESSING") {
          setCurrentScreen("upload");
          return;
        }

        if (
          session.status === "SUMMARY_READY" ||
          session.status === "QUEUED" ||
          session.status === "ASSIGNED" ||
          session.status === "CALLED" ||
          session.status === "IN_CONSULTATION" ||
          session.status === "COMPLETED"
        ) {
          setCurrentScreen("waiting");
          return;
        }

        clearStoredSessionId();
        setSessionId(null);
        setCurrentScreen("language");
      } catch {
        if (!active) {
          return;
        }

        clearStoredSessionId();
        setSessionId(null);
        setCurrentScreen("language");
        setSessionError(
          "Your previous session could not be restored. Please start again.",
        );
      } finally {
        if (active) {
          setIsRestoringSession(false);
        }
      }
    };

    void restoreSession();

    return () => {
      active = false;
    };
  }, []);

  const handleLanguageSelect = (selectedLanguage: "en" | "hi") => {
    setLanguage(selectedLanguage);
    setSessionError(null);
    setCurrentScreen("welcome");
  };

  const handleStart = async () => {
    if (isCreatingSession) {
      return;
    }

    setSessionError(null);
    setIsCreatingSession(true);
    setIdentityType(null);
    setIdentityIdentifier(null);
    setVisitType(null);
    setOtpChallengeId(null);
    setOtpDemoCode(null);
    setConsentVersion(null);
    setConsentText(null);

    try {
      const session = await createSession();
      storeSessionId(session.session_id);
      setSessionId(session.session_id);
      setCurrentScreen("identity");
    } catch (error) {
      setSessionError(
        error instanceof Error ? error.message : "Unable to start your session",
      );
    } finally {
      setIsCreatingSession(false);
    }
  };

  const handleBack = async () => {
    if (isNavigatingBack || isCreatingSession || isVerifying) {
      return;
    }

    if (currentScreen === "language") {
      return;
    }

    if (!sessionId) {
      if (currentScreen === "welcome") {
        setCurrentScreen("language");
      }

      return;
    }

    setIsNavigatingBack(true);

    try {
      const session = await getSession(sessionId);

      switch (currentScreen) {
        case "welcome":
          setCurrentScreen("language");
          break;

        case "identity":
          if (
            session.status === "CREATED" ||
            session.status === "IDENTIFYING"
          ) {
            setCurrentScreen("welcome");
          }
          break;

        case "consent":
          if (
            session.status === "IDENTIFYING" &&
            session.consent_status === "PENDING"
          ) {
            setCurrentScreen("identity");
          }
          break;

        case "ai-mode":
          if (session.status === "CONSENTED") {
            setCurrentScreen("consent");
          }
          break;

        case "ai-voice":
        case "ai-text":
          if (
            session.status === "CONSENTED" ||
            session.status === "HISTORY_IN_PROGRESS"
          ) {
            setCurrentScreen("ai-mode");
          }
          break;

        case "upload":
          if (session.status === "HISTORY_IN_PROGRESS") {
            setCurrentScreen("ai-mode");
          }
          break;

        case "waiting":
          if (session.status === "DOCUMENT_PROCESSING") {
            setCurrentScreen("upload");
          }
          break;

        default:
          break;
      }
    } catch {
      return;
    } finally {
      setIsNavigatingBack(false);
    }
  };

  const handleIdentityVerification = async (
    selectedIdentityType: "abha" | "aadhaar",
    identifier: string,
  ): Promise<boolean> => {
    if (!sessionId || isVerifying) {
      return false;
    }

    setVerificationError(null);
    setIsVerifying(true);

    try {
      const challenge = await requestIdentityOtp(
        sessionId,
        selectedIdentityType.toUpperCase(),
        identifier,
      );

      setIdentityType(selectedIdentityType);
      setIdentityIdentifier(identifier);
      setOtpChallengeId(challenge.challenge_id);
      setOtpDemoCode(challenge.demo_otp);

      return true;
    } catch (error) {
      setVerificationError(
        error instanceof Error ? error.message : "Unable to send OTP",
      );

      return false;
    } finally {
      setIsVerifying(false);
    }
  };

  const handleOtpVerification = async (otp: string) => {
    if (!sessionId || !otpChallengeId || isVerifying) {
      return;
    }

    setVerificationError(null);
    setIsVerifying(true);

    try {
      const identification = await verifyPatientOtp(
        sessionId,
        otpChallengeId,
        otp,
      );

      if (identification.status !== "VERIFIED") {
        throw new Error("Identity verification failed");
      }

      const consent = await getConsentInformation(sessionId);

      setVisitType(identification.visit_type);
      setConsentVersion(consent.version);
      setConsentText(consent.text);
      setOtpChallengeId(null);
      setOtpDemoCode(null);
      setCurrentScreen("consent");
    } catch (error) {
      setVerificationError(
        error instanceof Error ? error.message : "Identity verification failed",
      );
    } finally {
      setIsVerifying(false);
    }
  };

  const handleConsentGrant = async () => {
    if (
      !sessionId ||
      !consentVersion ||
      !identityType ||
      !identityIdentifier ||
      isRecordingConsent ||
      consentSubmissionLock.current
    ) {
      return;
    }

    consentSubmissionLock.current = true;
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
      consentSubmissionLock.current = false;
      setConsentError(
        error instanceof Error ? error.message : "Unable to record consent",
      );
    } finally {
      setIsRecordingConsent(false);
    }
  };

  const handleConsentDecline = async () => {
    if (
      !sessionId ||
      !consentVersion ||
      isRecordingConsent ||
      consentSubmissionLock.current
    ) {
      return;
    }

    consentSubmissionLock.current = true;
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
      consentSubmissionLock.current = false;
      setConsentError(
        error instanceof Error
          ? error.message
          : "Unable to record your response",
      );
    } finally {
      setIsRecordingConsent(false);
    }
  };

  return {
    currentScreen,
    language,
    sessionId,
    visitType,
    otpChallengeId,
    otpDemoCode,
    consentVersion,
    consentText,
    isCreatingSession,
    sessionError,
    isVerifying,
    verificationError,
    isRecordingConsent,
    consentError,
    isRestoringSession,
    isNavigatingBack,
    handleLanguageSelect,
    handleStart,
    handleBack,
    handleIdentityVerification,
    handleOtpVerification,
    handleConsentGrant,
    handleConsentDecline,
    resetFlow,
    setCurrentScreen,
  };
}
