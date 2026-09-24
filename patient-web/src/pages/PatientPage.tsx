import { useEffect, useState } from "react";
import { Moon, RefreshCw, Sun, UserPlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PatientBackButton } from "@/components/PatientBackButton";
import { usePatientFlow } from "@/hooks/usePatientFlow";
import { ConsentScreen } from "@/screens/ConsentScreen";
import { DocumentUpload } from "@/screens/DocumentUpload";
import { IdentitySelection } from "@/screens/IdentitySelection";
import { LanguageSelection } from "@/screens/LanguageSelection";
import { ThankYouScreen } from "@/screens/ThankYouScreen";
import { TextAIConsultation } from "@/screens/TextAIConsultation";
import { VoiceAIConsultation } from "@/screens/VoiceAIConsultation";
import { WaitingScreen } from "@/screens/WaitingScreen";
import { WelcomeScreen } from "@/screens/WelcomeScreen";

export function PatientPage() {
  const [theme, setTheme] = useState<"light" | "dark">("light");

  const {
    currentScreen,
    language,
    draftId,
    sessionId,
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

  const headerActionDisabled = isSubmittingRegistration || isStartingNewPatient;

  return (
    <div className="min-h-screen bg-bg text-text-primary transition-colors duration-300">
      <header className="flex items-center justify-between border-b border-border p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-accent">
            <span className="text-sm font-bold text-white">A</span>
          </div>

          <h1 className="text-xl font-semibold text-text-primary">Aurora</h1>
        </div>

        <div className="flex items-center gap-3">
          <Button
            className="rounded-full border-border bg-surface px-5"
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
            className="rounded-full border-border bg-surface"
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
            language={language}
            onClick={handleBack}
          />
        )}

        {currentScreen === "language" && (
          <LanguageSelection onNext={handleLanguageSelect} />
        )}

        {currentScreen === "welcome" && (
          <WelcomeScreen language={language} onNext={handleStart} />
        )}

        {currentScreen === "identity" && draftId && (
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
          (isLoadingConsent ? (
            <div className="flex min-h-[75vh] items-center justify-center">
              <div className="rounded-2xl border-2 border-border bg-surface px-10 py-8 text-center shadow-lg">
                <div className="mb-3 text-2xl font-bold">
                  {language === "hi"
                    ? "सहमति जानकारी लोड हो रही है..."
                    : "Loading consent information..."}
                </div>

                <div className="text-lg text-text-secondary">
                  {language === "hi"
                    ? "कृपया कुछ क्षण प्रतीक्षा करें।"
                    : "Please wait a moment."}
                </div>
              </div>
            </div>
          ) : consentVersion && consentText ? (
            <ConsentScreen
              language={language}
              consentText={consentText}
              consentVersion={consentVersion}
              error={consentError}
              onDecline={handleConsentDecline}
              onNext={handleConsentGrant}
            />
          ) : (
            <div className="flex min-h-[75vh] items-center justify-center px-4">
              <div className="max-w-xl rounded-2xl border-2 border-danger bg-surface p-8 text-center shadow-lg">
                <h2 className="mb-3 text-2xl font-bold text-text-primary">
                  {language === "hi"
                    ? "सहमति जानकारी उपलब्ध नहीं है"
                    : "Consent information is unavailable"}
                </h2>

                <p className="mb-6 text-lg text-text-secondary">
                  {consentError ??
                    (language === "hi"
                      ? "कृपया फिर से प्रयास करें।"
                      : "Please try again.")}
                </p>

                <Button
                  className="rounded-xl bg-primary-dark px-8 py-5 text-lg text-white shadow-lg hover:bg-text-primary"
                  onClick={() => {
                    void resetFlow();
                  }}
                >
                  <RefreshCw className="mr-2 h-5 w-5" />
                  {language === "hi" ? "फिर से शुरू करें" : "Start Again"}
                </Button>
              </div>
            </div>
          ))}

        {currentScreen === "ai-mode" && (
          <div className="flex h-[75vh] flex-col items-center justify-center">
            <div className="mb-12 space-y-4 text-center">
              <h2 className="text-4xl font-bold text-text-primary">
                {language === "hi"
                  ? "कैसे परामर्श करना चाहेंगे?"
                  : "How would you like to consult?"}
              </h2>

              <p className="text-xl text-text-secondary">
                {language === "hi"
                  ? "AI सहायक के साथ बातचीत का अपना तरीका चुनें"
                  : "Choose your preferred way to interact with AI"}
              </p>
            </div>

            <div className="grid w-full max-w-4xl grid-cols-1 gap-8 px-4 md:grid-cols-2">
              <Button
                type="button"
                variant="outline"
                className="flex h-64 w-full flex-col items-center justify-center gap-6 rounded-2xl border-2 border-border bg-surface text-text-primary transition-all duration-200 hover:scale-[1.02] hover:border-primary hover:bg-primary-tint active:scale-[0.98]"
                onClick={() => {
                  registerActivity();
                  setCurrentScreen("ai-voice");
                }}
              >
                <div className="flex h-20 w-20 items-center justify-center rounded-full bg-primary-tint">
                  <svg
                    className="h-10 w-10 text-primary-dark"
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

                <div className="text-3xl font-semibold text-text-primary">
                  {language === "hi" ? "वॉयस" : "Voice"}
                </div>

                <div className="text-lg text-text-secondary">
                  {language === "hi" ? "बोलकर बताएं" : "Speak naturally"}
                </div>
              </Button>

              <Button
                type="button"
                variant="outline"
                className="flex h-64 w-full flex-col items-center justify-center gap-6 rounded-2xl border-2 border-border bg-surface text-text-primary transition-all duration-200 hover:scale-[1.02] hover:border-primary hover:bg-primary-tint active:scale-[0.98]"
                onClick={() => {
                  registerActivity();
                  setCurrentScreen("ai-text");
                }}
              >
                <div className="flex h-20 w-20 items-center justify-center rounded-full bg-primary-tint">
                  <svg
                    className="h-10 w-10 text-primary-dark"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      d="M8 10h.01M12 10h.01M16 10.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                    />
                  </svg>
                </div>

                <div className="text-3xl font-semibold text-text-primary">
                  {language === "hi" ? "टेक्स्ट" : "Text"}
                </div>

                <div className="text-lg text-text-secondary">
                  {language === "hi" ? "टाइप करके बताएं" : "Type your symptoms"}
                </div>
              </Button>
            </div>
          </div>
        )}

        {currentScreen === "ai-voice" && draftId && sessionId && (
          <VoiceAIConsultation
            draftId={draftId}
            sessionId={sessionId}
            language={language}
            onActivity={registerActivity}
            onConversationTurn={handleConversationTurn}
            onNext={() => setCurrentScreen("upload")}
          />
        )}

        {currentScreen === "ai-text" && draftId && sessionId && (
          <TextAIConsultation
            draftId={draftId}
            sessionId={sessionId}
            language={language}
            onConversationTurn={handleConversationTurn}
            onNext={() => setCurrentScreen("upload")}
          />
        )}

        {currentScreen === "upload" && draftId && (
          <DocumentUpload
            draftId={draftId}
            language={language}
            onActivity={registerActivity}
            onNext={() => setCurrentScreen("thank-you")}
          />
        )}

        {currentScreen === "thank-you" && (
          <ThankYouScreen
            language={language}
            isSubmitting={isSubmittingRegistration}
            submitted={registrationSubmitted}
            error={registrationError}
            completionSecondsRemaining={completionSecondsRemaining}
            onSubmit={handleFinalizeRegistration}
            onContinue={handleContinueToWaiting}
            onReset={resetFlow}
          />
        )}

        {currentScreen === "waiting" && (
          <WaitingScreen
            language={language}
            onReset={resetFlow}
            timeLeft={completionSecondsRemaining}
          />
        )}
      </main>

      {showInactivityWarning && currentScreen !== "waiting" && (
        <div className="fixed bottom-6 left-1/2 z-40 -translate-x-1/2 rounded-full border-2 border-warning bg-surface px-6 py-3 text-center text-sm font-semibold text-text-primary shadow-xl">
          {language === "hi"
            ? `यह कियोस्क ${idleSecondsRemaining} सेकंड में निष्क्रियता के कारण रीसेट होगा`
            : `This kiosk will reset in ${idleSecondsRemaining} seconds due to inactivity`}
        </div>
      )}
    </div>
  );
}
