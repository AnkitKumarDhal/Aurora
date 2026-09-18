import { useEffect, useState } from "react";
import { Moon, Sun, UserPlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PatientBackButton } from "@/components/PatientBackButton";
import { usePatientFlow } from "@/hooks/usePatientFlow";
import { ConsentScreen } from "@/screens/ConsentScreen";
import { DocumentUpload } from "@/screens/DocumentUpload";
import { IdentitySelection } from "@/screens/IdentitySelection";
import { LanguageSelection } from "@/screens/LanguageSelection";
import { TextAIConsultation } from "@/screens/TextAIConsultation";
import { VoiceAIConsultation } from "@/screens/VoiceAIConsultation";
import { WaitingScreen } from "@/screens/WaitingScreen";
import { WelcomeScreen } from "@/screens/WelcomeScreen";

export function PatientPage() {
  const [theme, setTheme] = useState<"light" | "dark">("light");

  const {
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
    idleSecondsRemaining,
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
  } = usePatientFlow();

  useEffect(() => {
    window.document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  const toggleTheme = () => {
    setTheme((currentTheme) => (currentTheme === "light" ? "dark" : "light"));
  };

  const showBackButton =
    currentScreen === "welcome" ||
    currentScreen === "ai-voice" ||
    currentScreen === "ai-text" ||
    currentScreen === "upload";

  const showInactivityWarning =
    idleSecondsRemaining !== null &&
    idleSecondsRemaining <= 30 &&
    idleSecondsRemaining > 0;

  const headerActionDisabled =
    isCreatingSession ||
    isVerifying ||
    isRecordingConsent ||
    isNavigatingBack ||
    isStartingNewPatient;

  if (isRestoringSession) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-[var(--color-bg)] text-[var(--color-text-primary)]">
        <div className="rounded-2xl border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-10 py-8 text-center shadow-lg">
          <div className="mb-3 text-2xl font-bold">
            {language === "hi"
              ? "पिछला सत्र पुनर्स्थापित हो रहा है..."
              : "Restoring your session..."}
          </div>

          <div className="text-lg text-[var(--color-text-secondary)]">
            {language === "hi"
              ? "कृपया कुछ क्षण प्रतीक्षा करें।"
              : "Please wait a moment."}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--color-bg)] text-[var(--color-text-primary)] transition-colors duration-300">
      <header className="flex items-center justify-between border-b border-[var(--color-border)] p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)]">
            <span className="text-sm font-bold text-white">A</span>
          </div>

          <h1 className="text-xl font-semibold text-[var(--color-text-primary)]">
            Aurora
          </h1>
        </div>

        <div className="flex items-center gap-3">
          <Button
            className="rounded-full border-[var(--color-border)] bg-[var(--color-surface)] px-5"
            disabled={headerActionDisabled}
            onClick={() => {
              void handleNewPatient();
            }}
            variant="outline"
          >
            <UserPlus className="mr-2 h-4 w-4" />
            {isStartingNewPatient
              ? language === "hi"
                ? "रीसेट हो रहा है..."
                : "Resetting..."
              : language === "hi"
                ? "नया रोगी"
                : "New Patient"}
          </Button>

          <Button
            className="rounded-full border-[var(--color-border)] bg-[var(--color-surface)]"
            onClick={toggleTheme}
            size="icon"
            variant="outline"
          >
            {theme === "light" ? (
              <Moon className="h-4 w-4" />
            ) : (
              <Sun className="h-4 w-4" />
            )}
          </Button>
        </div>
      </header>

      <main className="relative container mx-auto max-w-5xl p-6 md:p-12">
        {showBackButton && (
          <PatientBackButton
            className="absolute left-6 top-6 z-20 md:left-12 md:top-12"
            disabled={isNavigatingBack || isCreatingSession || isVerifying}
            language={language}
            onClick={handleBack}
          />
        )}

        {currentScreen === "language" && (
          <LanguageSelection onNext={handleLanguageSelect} />
        )}

        {currentScreen === "welcome" && (
          <div className="relative">
            {sessionError && (
              <div className="mb-6 rounded-xl border-2 border-[var(--color-danger)] bg-[var(--color-surface)] px-6 py-4 text-center text-[var(--color-danger)]">
                {sessionError}
              </div>
            )}

            <WelcomeScreen language={language} onNext={handleStart} />

            {isCreatingSession && (
              <div className="pointer-events-none absolute inset-x-0 bottom-8 flex justify-center">
                <div className="rounded-full bg-[var(--color-primary-tint)] px-5 py-3 text-sm font-semibold text-[var(--color-primary-dark)] shadow-lg">
                  {language === "hi"
                    ? "सत्र शुरू हो रहा है..."
                    : "Starting your session..."}
                </div>
              </div>
            )}
          </div>
        )}

        {currentScreen === "identity" && sessionId && (
          <IdentitySelection
            language={language}
            isVerifying={isVerifying}
            error={verificationError}
            otpChallengeId={otpChallengeId}
            otpDemoCode={otpDemoCode}
            onBack={handleBack}
            onNext={handleIdentityVerification}
            onVerifyOtp={handleOtpVerification}
          />
        )}

        {currentScreen === "consent" &&
          sessionId &&
          consentVersion &&
          consentText && (
            <ConsentScreen
              language={language}
              consentText={consentText}
              consentVersion={consentVersion}
              visitType={visitType}
              isSubmitting={isRecordingConsent}
              error={consentError}
              onDecline={handleConsentDecline}
              onNext={handleConsentGrant}
            />
          )}

        {currentScreen === "ai-mode" && (
          <div className="flex h-[75vh] flex-col items-center justify-center">
            <div className="mb-12 space-y-4 text-center">
              <h2 className="text-4xl font-bold text-[var(--color-text-primary)]">
                {language === "hi"
                  ? "कैसे परामर्श करना चाहेंगे?"
                  : "How would you like to consult?"}
              </h2>

              <p className="text-xl text-[var(--color-text-secondary)]">
                {language === "hi"
                  ? "AI सहायक के साथ बातचीत का अपना तरीका चुनें"
                  : "Choose your preferred way to interact with AI"}
              </p>
            </div>

            <div className="grid w-full max-w-4xl grid-cols-1 gap-8 px-4 md:grid-cols-2">
              <button
                className="flex h-64 flex-col items-center justify-center gap-6 rounded-2xl border-2 border-[var(--color-border)] bg-[var(--color-surface)] transition-all hover:border-[var(--color-primary)]"
                onClick={() => {
                  registerActivity();
                  setCurrentScreen("ai-voice");
                }}
                type="button"
              >
                <div className="flex h-20 w-20 items-center justify-center rounded-full bg-[var(--color-primary-tint)]">
                  <svg
                    className="h-10 w-10 text-[var(--color-primary-dark)]"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                    />
                  </svg>
                </div>

                <div className="text-3xl font-semibold text-[var(--color-text-primary)]">
                  {language === "hi" ? "वॉयस" : "Voice"}
                </div>

                <div className="text-lg text-[var(--color-text-secondary)]">
                  {language === "hi" ? "बोलकर बताएं" : "Speak naturally"}
                </div>
              </button>

              <button
                className="flex h-64 flex-col items-center justify-center gap-6 rounded-2xl border-2 border-[var(--color-border)] bg-[var(--color-surface)] transition-all hover:border-[var(--color-primary)]"
                onClick={() => {
                  registerActivity();
                  setCurrentScreen("ai-text");
                }}
                type="button"
              >
                <div className="flex h-20 w-20 items-center justify-center rounded-full bg-[var(--color-primary-tint)]">
                  <svg
                    className="h-10 w-10 text-[var(--color-primary-dark)]"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                    />
                  </svg>
                </div>

                <div className="text-3xl font-semibold text-[var(--color-text-primary)]">
                  {language === "hi" ? "टेक्स्ट" : "Text"}
                </div>

                <div className="text-lg text-[var(--color-text-secondary)]">
                  {language === "hi" ? "टाइप करके बताएं" : "Type your symptoms"}
                </div>
              </button>
            </div>
          </div>
        )}

        {currentScreen === "ai-voice" && sessionId && (
          <VoiceAIConsultation
            sessionId={sessionId}
            language={language}
            onActivity={registerActivity}
            onNext={() => setCurrentScreen("upload")}
          />
        )}

        {currentScreen === "ai-text" && sessionId && (
          <TextAIConsultation
            sessionId={sessionId}
            language={language}
            onNext={() => setCurrentScreen("upload")}
          />
        )}

        {currentScreen === "upload" && sessionId && (
          <DocumentUpload
            sessionId={sessionId}
            language={language}
            onNext={() => setCurrentScreen("waiting")}
          />
        )}

        {currentScreen === "waiting" && (
          <WaitingScreen language={language} onReset={resetFlow} />
        )}
      </main>

      {showInactivityWarning && (
        <div className="fixed bottom-6 left-1/2 z-40 -translate-x-1/2 rounded-full border-2 border-[var(--color-warning)] bg-[var(--color-surface)] px-6 py-3 text-center text-sm font-semibold text-[var(--color-text-primary)] shadow-xl">
          {language === "hi"
            ? `यह कियोस्क ${idleSecondsRemaining} सेकंड में निष्क्रियता के कारण रीसेट होगा`
            : `This kiosk will reset in ${idleSecondsRemaining} seconds due to inactivity`}
        </div>
      )}
    </div>
  );
}
