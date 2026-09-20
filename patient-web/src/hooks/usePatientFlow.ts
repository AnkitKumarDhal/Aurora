import { useCallback, useEffect, useRef, useState } from "react";
import { getConsentInformation, recordConsent } from "@/api/consent";
import {
  prepareInterviewSession,
  submitInterviewTurn,
  type InterviewTurnResult,
} from "@/api/interview";
import { completePatientIntake } from "@/api/intake";
import {
  submitPatientRegistration,
  type RegistrationResponse,
} from "@/api/registration";
import {
  requestPatientVerificationOtp,
  verifyPatientIdentityOtp,
} from "@/api/patientVerification";
import { abandonSession } from "@/api/sessions";
import {
  appendPatientDraftConversationTurn,
  clearPatientDraftStorage,
  createPatientDraft,
  loadPatientDraft,
  listPatientDraftDocuments,
  savePatientDraft,
  type PatientDraftConversationInputType,
  type PatientDraftIdentityMethod,
} from "@/lib/patientDraft";

const IDLE_TIMEOUT_SECONDS = 90;
const COMPLETION_TIMEOUT_SECONDS = 90;

export type PatientScreen =
  | "language"
  | "welcome"
  | "identity"
  | "consent"
  | "ai-mode"
  | "ai-voice"
  | "ai-text"
  | "upload"
  | "thank-you"
  | "waiting";

export type PatientVisitType = "FIRST_VISIT" | "RETURNING_VISIT" | null;

export function usePatientFlow() {
  const [currentScreen, setCurrentScreen] = useState<PatientScreen>("language");
  const [language, setLanguage] = useState<"en" | "hi">("en");
  const [draftId, setDraftId] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [identityType, setIdentityType] =
    useState<PatientDraftIdentityMethod | null>(null);
  const [identityIdentifier, setIdentityIdentifier] = useState<string | null>(
    null,
  );
  const [otpChallengeId, setOtpChallengeId] = useState<string | null>(null);
  const [otpDemoCode, setOtpDemoCode] = useState<string | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationError, setVerificationError] = useState<string | null>(
    null,
  );
  const [consentVersion, setConsentVersion] = useState<string | null>(null);
  const [consentText, setConsentText] = useState<string | null>(null);
  const [isLoadingConsent, setIsLoadingConsent] = useState(false);
  const [consentError, setConsentError] = useState<string | null>(null);
  const [isSubmittingRegistration, setIsSubmittingRegistration] =
    useState(false);
  const [registrationError, setRegistrationError] = useState<string | null>(
    null,
  );
  const [registrationSubmitted, setRegistrationSubmitted] = useState(false);
  const [isStartingNewPatient, setIsStartingNewPatient] = useState(false);
  const [idleSecondsRemaining, setIdleSecondsRemaining] =
    useState(IDLE_TIMEOUT_SECONDS);
  const [completionSecondsRemaining, setCompletionSecondsRemaining] = useState(
    COMPLETION_TIMEOUT_SECONDS,
  );

  const newPatientResetLock = useRef(false);
  const registrationSubmissionLock = useRef(false);
  const lastActivityAt = useRef(0);

  const resetFlow = useCallback(async () => {
    const activeDraftId = draftId;
    await clearPatientDraftStorage(activeDraftId);

    if (sessionId) {
      await abandonSession(sessionId).catch(() => undefined);
    }

    newPatientResetLock.current = false;
    registrationSubmissionLock.current = false;

    setCurrentScreen("language");
    setLanguage("en");
    setDraftId(null);
    setSessionId(null);
    setIdentityType(null);
    setIdentityIdentifier(null);
    setOtpChallengeId(null);
    setOtpDemoCode(null);
    setConsentVersion(null);
    setConsentText(null);
    setVerificationError(null);
    setConsentError(null);
    setRegistrationError(null);
    setRegistrationSubmitted(false);
    setIsVerifying(false);
    setIsLoadingConsent(false);
    setIsSubmittingRegistration(false);
    setIsStartingNewPatient(false);
    setIdleSecondsRemaining(IDLE_TIMEOUT_SECONDS);
    setCompletionSecondsRemaining(COMPLETION_TIMEOUT_SECONDS);

    lastActivityAt.current = Date.now();
  }, [draftId, sessionId]);

  const registerActivity = useCallback(() => {
    lastActivityAt.current = Date.now();
    setIdleSecondsRemaining(IDLE_TIMEOUT_SECONDS);
  }, []);

  const handleLanguageSelect = useCallback(
    (selectedLanguage: "en" | "hi") => {
      registerActivity();
      setLanguage(selectedLanguage);
      setCurrentScreen("welcome");
    },
    [registerActivity],
  );

  const handleStart = useCallback(async () => {
    if (isStartingNewPatient || isSubmittingRegistration) {
      return;
    }

    const previousDraft = loadPatientDraft();

    if (previousDraft) {
      await clearPatientDraftStorage(previousDraft.draft_id);
    } else {
      await clearPatientDraftStorage(null);
    }

    const draft = createPatientDraft(language);

    savePatientDraft(draft);

    setDraftId(draft.draft_id);
    setSessionId(null);
    setIdentityType(null);
    setIdentityIdentifier(null);
    setOtpChallengeId(null);
    setOtpDemoCode(null);
    setConsentVersion(null);
    setConsentText(null);
    setVerificationError(null);
    setConsentError(null);
    setRegistrationError(null);
    setRegistrationSubmitted(false);
    setCompletionSecondsRemaining(COMPLETION_TIMEOUT_SECONDS);

    registerActivity();
    setCurrentScreen("identity");
  }, [
    isStartingNewPatient,
    isSubmittingRegistration,
    language,
    registerActivity,
  ]);

  const handleBack = useCallback(async () => {
    registerActivity();

    if (currentScreen === "welcome") {
      setCurrentScreen("language");
      return;
    }

    if (currentScreen === "identity") {
      await clearPatientDraftStorage(draftId);
      setDraftId(null);
      setSessionId(null);
      setIdentityType(null);
      setIdentityIdentifier(null);
      setOtpChallengeId(null);
      setOtpDemoCode(null);
      setVerificationError(null);
      setCurrentScreen("language");
      return;
    }

    if (currentScreen === "ai-voice" || currentScreen === "ai-text") {
      setCurrentScreen("ai-mode");
      return;
    }

    if (currentScreen === "upload") {
      setCurrentScreen("ai-mode");
    }
  }, [currentScreen, draftId, registerActivity]);

  const handleNewPatient = useCallback(async () => {
    if (newPatientResetLock.current || isSubmittingRegistration) {
      return;
    }

    newPatientResetLock.current = true;
    setIsStartingNewPatient(true);
    await resetFlow();
  }, [isSubmittingRegistration, resetFlow]);

  const handleInactivityTimeout = useCallback(async () => {
    if (newPatientResetLock.current || isSubmittingRegistration) {
      return;
    }

    newPatientResetLock.current = true;
    setIsStartingNewPatient(true);
    await resetFlow();
  }, [isSubmittingRegistration, resetFlow]);

  useEffect(() => {
    if (
      currentScreen === "waiting" ||
      currentScreen === "thank-you" ||
      currentScreen === "language" ||
      isVerifying ||
      isLoadingConsent ||
      isSubmittingRegistration ||
      isStartingNewPatient
    ) {
      return;
    }

    if (lastActivityAt.current === 0) {
      lastActivityAt.current = Date.now();
    }

    const timer = window.setInterval(() => {
      const elapsedSeconds = Math.floor(
        (Date.now() - lastActivityAt.current) / 1000,
      );

      const remaining = Math.max(0, IDLE_TIMEOUT_SECONDS - elapsedSeconds);
      setIdleSecondsRemaining(remaining);

      if (remaining <= 0) {
        window.clearInterval(timer);
        void handleInactivityTimeout();
      }
    }, 1000);

    return () => window.clearInterval(timer);
  }, [
    currentScreen,
    handleInactivityTimeout,
    isLoadingConsent,
    isStartingNewPatient,
    isSubmittingRegistration,
    isVerifying,
  ]);

  useEffect(() => {
    if (!registrationSubmitted) {
      return;
    }

    const timer = window.setInterval(() => {
      setCompletionSecondsRemaining((previous) => {
        const next = Math.max(0, previous - 1);

        if (next <= 0) {
          window.clearInterval(timer);
          void resetFlow();
        }

        return next;
      });
    }, 1000);

    return () => window.clearInterval(timer);
  }, [registrationSubmitted, resetFlow]);

  const handleIdentityVerification = useCallback(
    async (
      selectedIdentityType: "abha" | "aadhaar",
      identifier: string,
    ): Promise<boolean> => {
      if (!draftId || isVerifying) {
        return false;
      }

      registerActivity();
      setVerificationError(null);
      setIsVerifying(true);

      try {
        const method =
          selectedIdentityType.toUpperCase() as PatientDraftIdentityMethod;

        const challenge = await requestPatientVerificationOtp(
          draftId,
          method,
          identifier,
        );

        const draft = loadPatientDraft();

        if (!draft || draft.draft_id !== draftId) {
          throw new Error("Patient draft could not be found");
        }

        savePatientDraft({
          ...draft,
          identity_method: method,
          identity_identifier: identifier,
          verification_token: null,
        });

        setIdentityType(method);
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
    },
    [draftId, isVerifying, registerActivity],
  );

  const handleOtpVerification = useCallback(
    async (otp: string) => {
      if (!draftId || !otpChallengeId || isVerifying) {
        return;
      }

      registerActivity();
      setVerificationError(null);
      setConsentError(null);
      setIsVerifying(true);

      try {
        const verification = await verifyPatientIdentityOtp(
          draftId,
          otpChallengeId,
          otp,
        );

        if (verification.status !== "VERIFIED") {
          throw new Error("Identity verification failed");
        }

        const draft = loadPatientDraft();

        if (!draft || draft.draft_id !== draftId) {
          throw new Error("Patient draft could not be found");
        }

        if (!identityType || !identityIdentifier) {
          throw new Error("Identity information is missing");
        }

        savePatientDraft({
          ...draft,
          verification_token: verification.verification_token,
        });

        const preparedSession = await prepareInterviewSession(
          draftId,
          verification.verification_token,
          identityType,
          identityIdentifier,
        );

        setSessionId(preparedSession.session_id);
        setOtpChallengeId(null);
        setOtpDemoCode(null);
        setIsLoadingConsent(true);
        setCurrentScreen("consent");

        const consent = await getConsentInformation();

        setConsentVersion(consent.version);
        setConsentText(consent.text);
        setConsentError(null);
      } catch (error) {
        setVerificationError(
          error instanceof Error
            ? error.message
            : "Identity verification failed",
        );

        setConsentError(
          error instanceof Error
            ? error.message
            : "Unable to prepare your interview session",
        );
      } finally {
        setIsLoadingConsent(false);
        setIsVerifying(false);
      }
    },
    [
      draftId,
      identityIdentifier,
      identityType,
      isVerifying,
      otpChallengeId,
      registerActivity,
    ],
  );

  const handleConsentGrant = useCallback(async () => {
    if (
      !draftId ||
      !sessionId ||
      !consentVersion ||
      !identityType ||
      !identityIdentifier
    ) {
      return;
    }

    const draft = loadPatientDraft();

    if (!draft || draft.draft_id !== draftId || !draft.verification_token) {
      setConsentError("Your verification has expired. Please start again.");
      return;
    }

    try {
      registerActivity();

      const result = await recordConsent(
        sessionId,
        consentVersion,
        identityType,
        identityIdentifier,
      );

      if (result.consent_status !== "GRANTED") {
        throw new Error("Consent could not be recorded");
      }

      savePatientDraft({
        ...draft,
        consent_version: consentVersion,
        consent_granted: true,
      });

      setConsentError(null);
      setCurrentScreen("ai-mode");
    } catch (error) {
      setConsentError(
        error instanceof Error
          ? error.message
          : "Unable to record your consent",
      );
    }
  }, [
    consentVersion,
    draftId,
    identityIdentifier,
    identityType,
    registerActivity,
    sessionId,
  ]);

  const handleConsentDecline = useCallback(async () => {
    registerActivity();
    await resetFlow();
  }, [registerActivity, resetFlow]);

  const handleConversationTurn = useCallback(
    async (
      inputType: PatientDraftConversationInputType,
      content: string,
      turnLanguage: string,
    ): Promise<InterviewTurnResult | null> => {
      if (!draftId || !sessionId) {
        return null;
      }

      const draft = loadPatientDraft();

      if (!draft || draft.draft_id !== draftId) {
        return null;
      }

      try {
        const updatedDraft = appendPatientDraftConversationTurn(draft, {
          input_type: inputType,
          content,
          language: turnLanguage,
        });

        const localTurn =
          updatedDraft.conversation_turns[
            updatedDraft.conversation_turns.length - 1
          ];

        if (!localTurn) {
          return null;
        }

        const result = await submitInterviewTurn(
          sessionId,
          draftId,
          localTurn.local_id,
          inputType,
          content,
          turnLanguage,
        );

        registerActivity();

        return result;
      } catch {
        return null;
      }
    },
    [draftId, registerActivity, sessionId],
  );

  const handleFinalizeRegistration = useCallback(async () => {
    if (
      !draftId ||
      !sessionId ||
      registrationSubmissionLock.current ||
      registrationSubmitted
    ) {
      return;
    }

    registrationSubmissionLock.current = true;
    setIsSubmittingRegistration(true);
    setRegistrationError(null);

    try {
      const draft = loadPatientDraft();

      if (!draft || draft.draft_id !== draftId) {
        throw new Error("Your patient information could not be found locally");
      }

      if (!draft.verification_token || !draft.consent_granted) {
        throw new Error("Identity verification and consent are required");
      }

      if (!draft.identity_method || !draft.identity_identifier) {
        throw new Error("Verified identity information is missing");
      }

      registerActivity();

      const documents = await listPatientDraftDocuments(draftId);

      const registration: RegistrationResponse =
        await submitPatientRegistration(draft, documents);

      const completion = await completePatientIntake(
        registration.session_id,
        draft.draft_id,
        draft.verification_token,
        draft.identity_method,
        draft.identity_identifier,
      );

      setSessionId(completion.session_id);
      setRegistrationSubmitted(true);
      setOtpChallengeId(null);
      setOtpDemoCode(null);
      setCompletionSecondsRemaining(COMPLETION_TIMEOUT_SECONDS);

      try {
        await clearPatientDraftStorage(null);
      } catch (cleanupError) {
        console.error(
          "Registration succeeded but local draft cleanup failed:",
          cleanupError,
        );
      }
    } catch (error) {
      setRegistrationError(
        error instanceof Error
          ? error.message
          : "Unable to complete your registration",
      );
    } finally {
      registrationSubmissionLock.current = false;
      setIsSubmittingRegistration(false);
    }
  }, [draftId, registerActivity, registrationSubmitted, sessionId]);

  const handleContinueToWaiting = useCallback(() => {
    if (!registrationSubmitted) {
      return;
    }

    setCurrentScreen("waiting");
  }, [registrationSubmitted]);

  const showInactivityWarning =
    idleSecondsRemaining <= 30 && idleSecondsRemaining > 0;

  return {
    currentScreen,
    language,
    draftId,
    sessionId,
    identityType,
    identityIdentifier,
    otpChallengeId,
    otpDemoCode,
    consentVersion,
    consentText,
    isVerifying,
    verificationError,
    isLoadingConsent,
    consentError,
    isSubmittingRegistration,
    registrationError,
    registrationSubmitted,
    isStartingNewPatient,
    idleSecondsRemaining,
    completionSecondsRemaining,
    showInactivityWarning,
    registerActivity,
    handleLanguageSelect,
    handleStart,
    handleBack,
    handleNewPatient,
    handleIdentityVerification,
    handleOtpVerification,
    handleConsentGrant,
    handleConsentDecline,
    handleConversationTurn,
    handleFinalizeRegistration,
    handleContinueToWaiting,
    resetFlow,
    setCurrentScreen,
  };
}
