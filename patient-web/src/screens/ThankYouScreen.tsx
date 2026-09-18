import { useEffect } from "react";
import { CheckCircle2, Loader2, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ThankYouScreenProps {
  language: "en" | "hi";
  isSubmitting: boolean;
  submitted: boolean;
  error: string | null;
  completionSecondsRemaining: number;
  onSubmit: () => void | Promise<void>;
  onContinue: () => void;
  onReset: () => void | Promise<void>;
}

export function ThankYouScreen({
  language,
  isSubmitting,
  submitted,
  error,
  completionSecondsRemaining,
  onSubmit,
  onContinue,
  onReset,
}: ThankYouScreenProps) {
  const isHi = language === "hi";

  useEffect(() => {
    if (!submitted || isSubmitting || error) {
      return;
    }

    const timer = window.setTimeout(() => {
      onContinue();
    }, 5000);

    return () => window.clearTimeout(timer);
  }, [error, isSubmitting, onContinue, submitted]);

  useEffect(() => {
    if (!submitted && !isSubmitting && !error) {
      void onSubmit();
    }
  }, [error, isSubmitting, onSubmit, submitted]);

  return (
    <div className="flex min-h-[75vh] w-full flex-col items-center justify-center px-4 text-center">
      <div className="mb-8 flex h-24 w-24 items-center justify-center rounded-full bg-primary-tint">
        {isSubmitting ? (
          <Loader2 className="h-12 w-12 animate-spin text-primary-dark" />
        ) : (
          <CheckCircle2 className="h-12 w-12 text-primary-dark" />
        )}
      </div>

      <h2 className="mb-4 text-4xl font-bold text-text-primary">
        {isHi ? "पंजीकरण के लिए धन्यवाद" : "Thank you for registering"}
      </h2>

      <p className="mb-8 max-w-2xl text-xl leading-relaxed text-text-secondary">
        {isSubmitting
          ? isHi
            ? "आपकी जानकारी अब अस्पताल के सिस्टम में सुरक्षित रूप से भेजी जा रही है।"
            : "Your information is now being securely submitted to the hospital system."
          : error
            ? isHi
              ? "आपकी जानकारी अभी सहेजी नहीं जा सकी। आपकी स्थानीय जानकारी सुरक्षित है।"
              : "Your information could not be saved yet. Your local information is still safe."
            : isHi
              ? "आपका पंजीकरण सुरक्षित रूप से पूरा हो गया है।"
              : "Your registration has been securely completed."}
      </p>

      {error && (
        <div className="mb-6 max-w-2xl rounded-xl border-2 border-danger bg-surface px-6 py-4 text-sm font-semibold text-danger">
          {error}
        </div>
      )}

      {submitted && !error && !isSubmitting && (
        <>
          <p className="mb-3 text-lg font-medium text-text-secondary">
            {isHi
              ? "आपको प्रतीक्षा क्षेत्र में ले जाया जाएगा।"
              : "You will be taken to the waiting area shortly."}
          </p>

          <p className="text-sm text-text-secondary">
            {isHi
              ? `कियोस्क ${completionSecondsRemaining} सेकंड में अगले रोगी के लिए रीसेट होगा`
              : `This kiosk will reset for the next patient in ${completionSecondsRemaining} seconds`}
          </p>
        </>
      )}

      {error && (
        <div className="flex gap-4">
          <Button
            className="rounded-xl bg-primary-dark px-8 py-5 text-lg text-white shadow-lg transition-all hover:bg-text-primary"
            onClick={() => {
              void onSubmit();
            }}
          >
            {isHi ? "पुनः प्रयास करें" : "Retry"}
          </Button>

          <Button
            className="rounded-xl border-2 border-border px-8 py-5 text-lg text-text-secondary hover:bg-surface-alt"
            onClick={() => {
              void onReset();
            }}
            variant="outline"
          >
            <RotateCcw className="mr-2 h-5 w-5" />
            {isHi ? "रीसेट करें" : "Reset"}
          </Button>
        </div>
      )}
    </div>
  );
}
