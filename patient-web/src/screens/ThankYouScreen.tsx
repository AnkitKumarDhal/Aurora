import { useEffect } from "react";
import { CheckCircle2, Loader2, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ThankYouScreenProps {
  language: "en" | "hi";
  isSubmitting: boolean;
  submitted: boolean;
  error: string | null;
  onSubmit: () => void | Promise<void>;
  onContinue: () => void;
  onReset: () => void | Promise<void>;
}

export function ThankYouScreen({
  language,
  isSubmitting,
  submitted,
  error,
  onSubmit,
  onContinue,
  onReset,
}: ThankYouScreenProps) {
  const isHi = language === "hi";

  useEffect(() => {
    if (!submitted && !isSubmitting && !error) {
      void onSubmit();
    }
  }, [error, isSubmitting, onSubmit, submitted]);

  return (
    <div className="flex min-h-[75vh] w-full flex-col items-center justify-center px-4 text-center">
      <div className="mb-8 flex h-24 w-24 items-center justify-center rounded-full bg-[var(--color-primary-tint)]">
        {isSubmitting ? (
          <Loader2 className="h-12 w-12 animate-spin text-[var(--color-primary-dark)]" />
        ) : (
          <CheckCircle2 className="h-12 w-12 text-[var(--color-primary-dark)]" />
        )}
      </div>

      <h2 className="mb-4 text-4xl font-bold text-[var(--color-text-primary)]">
        {isHi ? "पंजीकरण के लिए धन्यवाद" : "Thank you for registering"}
      </h2>

      <p className="mb-8 max-w-2xl text-xl leading-relaxed text-[var(--color-text-secondary)]">
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
        <div className="mb-6 max-w-2xl rounded-xl border-2 border-[var(--color-danger)] bg-[var(--color-surface)] px-6 py-4 text-sm font-semibold text-[var(--color-danger)]">
          {error}
        </div>
      )}

      {submitted ? (
        <Button
          className="rounded-xl bg-[var(--color-primary-dark)] px-10 py-6 text-xl text-white shadow-lg transition-all hover:bg-[var(--color-text-primary)]"
          onClick={onContinue}
        >
          {isHi ? "प्रतीक्षा क्षेत्र में जाएं" : "Continue to Waiting Area"}
        </Button>
      ) : error ? (
        <div className="flex gap-4">
          <Button
            className="rounded-xl bg-[var(--color-primary-dark)] px-8 py-5 text-lg text-white shadow-lg transition-all hover:bg-[var(--color-text-primary)]"
            onClick={() => {
              void onSubmit();
            }}
          >
            {isHi ? "पुनः प्रयास करें" : "Retry"}
          </Button>

          <Button
            className="rounded-xl border-2 border-[var(--color-border)] px-8 py-5 text-lg text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-alt)]"
            onClick={() => {
              void onReset();
            }}
            variant="outline"
          >
            <RotateCcw className="mr-2 h-5 w-5" />
            {isHi ? "रीसेट करें" : "Reset"}
          </Button>
        </div>
      ) : null}
    </div>
  );
}
