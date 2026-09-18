import { useCallback, useEffect, useRef, useState } from "react";
import { getConsentInformation, recordConsent } from "@/api/consent";
import { abandonSession, createSession, getSession } from "@/api/sessions";
import { requestIdentityOtp, verifyPatientOtp } from "@/api/verification";

const SESSION_STORAGE_KEY = "aurora.patient.session_id";
const IDLE_TIMEOUT_SECONDS = 90;

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
  const [isStartingNewPatient, setIsStartingNewPatient] = useState(false);
  const [idleSecondsRemaining, setIdleSecondsRemaining] = useState<
    number | null
  >(IDLE_TIMEOUT_SECONDS);

  const consentSubmissionLock = useRef(false);
  const newPatientResetLock = useRef(false);
  const lastActivityAt = useRef(0);

  const resetFlow = useCallback(() => {
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
    setIsStartingNewPatient(false);
    lastActivityAt.current = Date.now();
    setIdleSecondsRemaining(IDLE_TIMEOUT_SECONDS);
  }, []);

  const registerActivity = useCallback(() => {
    lastActivityAt.current = Date.now();

    if (currentScreen !== "waiting") {
      setIdleSecondsRemaining(IDLE_TIMEOUT_SECONDS);
    }
  }, [currentScreen]);

  useEffect(() => {
    const events = ["pointerdown", "keydown", "touchstart", "wheel"] as const;

    for (const event of events) {
      window.addEventListener(event, registerActivity, {
        passive: true,
      });
    }

    return () => {
      for (const event of events) {
        window.removeEventListener(event, registerActivity);
      }
    };
  }, [registerActivity]);

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
    registerActivity();
    setLanguage(selectedLanguage);
    setSessionError(null);
    setCurrentScreen("welcome");
  };

  const handleStart = async () => {
    if (isCreatingSession) {
      return;
    }

    registerActivity();
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

    registerActivity();

    if (currentScreen === "language") {
      return;
    }

    if (currentScreen === "welcome") {
      setCurrentScreen("language");
      return;
    }

    if (currentScreen === "identity") {
      setCurrentScreen("language");
      return;
    }

    if (!sessionId) {
      return;
    }

    setIsNavigatingBack(true);

    try {
      const session = await getSession(sessionId);

      switch (currentScreen) {
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
          if (
            session.status === "CONSENTED" ||
            session.status === "HISTORY_IN_PROGRESS" ||
            session.status === "DOCUMENT_PROCESSING"
          ) {
            setCurrentScreen("ai-mode");
          }
          break;

        default:
          break;
      }
    } finally {
      setIsNavigatingBack(false);
    }
  };

  const handleNewPatient = useCallback(async () => {
    if (newPatientResetLock.current) {
      return;
    }

    newPatientResetLock.current = true;
    registerActivity();
    setIsStartingNewPatient(true);

    const activeSessionId = sessionId;
    const shouldAbandon =
      activeSessionId !== null &&
      currentScreen !== "language" &&
      currentScreen !== "welcome" &&
      currentScreen !== "waiting";

    try {
      if (shouldAbandon && activeSessionId) {
        try {
          await abandonSession(activeSessionId);
        } catch (error) {
          console.error(
            "Unable to abandon the current patient session:",
            error,
          );
        }
      }
    } finally {
      newPatientResetLock.current = false;
      resetFlow();
    }
  }, [currentScreen, registerActivity, resetFlow, sessionId]);

  const handleInactivityTimeout = useCallback(async () => {
    if (newPatientResetLock.current) {
      return;
    }

    newPatientResetLock.current = true;
    setIsStartingNewPatient(true);

    const activeSessionId = sessionId;
    const shouldAbandon =
      activeSessionId !== null &&
      currentScreen !== "language" &&
      currentScreen !== "welcome" &&
      currentScreen !== "waiting";

    try {
      if (shouldAbandon && activeSessionId) {
        try {
          await abandonSession(activeSessionId);
        } catch (error) {
          console.error("Unable to abandon inactive patient session:", error);
        }
      }
    } finally {
      newPatientResetLock.current = false;
      resetFlow();
    }
  }, [currentScreen, resetFlow, sessionId]);

  useEffect(() => {
    const shouldPauseIdleTimer =
      isRestoringSession ||
      currentScreen === "waiting" ||
      isCreatingSession ||
      isVerifying ||
      isRecordingConsent ||
      isNavigatingBack ||
      isStartingNewPatient;

    if (shouldPauseIdleTimer) {
      return;
    }

    if (lastActivityAt.current === 0) {
      lastActivityAt.current = Date.now();
    }

    const interval = window.setInterval(() => {
      const elapsedSeconds = Math.floor(
        (Date.now() - lastActivityAt.current) / 1000,
      );
      const remaining = Math.max(0, IDLE_TIMEOUT_SECONDS - elapsedSeconds);

      setIdleSecondsRemaining(remaining);

      if (remaining <= 0) {
        window.clearInterval(interval);
        void handleInactivityTimeout();
      }
    }, 1000);

    return () => {
      window.clearInterval(interval);
    };
  }, [
    currentScreen,
    handleInactivityTimeout,
    isCreatingSession,
    isNavigatingBack,
    isRecordingConsent,
    isRestoringSession,
    isStartingNewPatient,
    isVerifying,
  ]);

  const visibleIdleSecondsRemaining =
    isRestoringSession ||
    currentScreen === "waiting" ||
    isCreatingSession ||
    isVerifying ||
    isRecordingConsent ||
    isNavigatingBack ||
    isStartingNewPatient
      ? null
      : idleSecondsRemaining;

  const handleIdentityVerification = async (
    selectedIdentityType: "abha" | "aadhaar",
    identifier: string,
  ): Promise<boolean> => {
    if (!sessionId || isVerifying) {
      return false;
    }

    registerActivity();
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

    registerActivity();
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

    registerActivity();
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

    registerActivity();
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
    isStartingNewPatient,
    idleSecondsRemaining: visibleIdleSecondsRemaining,
    registerActivity,
    handleLanguageSelect,
    handleStart,
    handleBack,
    handleNewPatient,
    handleIdentityVerification,
    handleOtpVerification,
    handleConsentGrant,
    handleConsentDecline,
    resetFlow,
    setCurrentScreen,
  };
}
