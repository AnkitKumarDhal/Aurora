import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { FileText, ShieldCheck } from "lucide-react";

interface ConsentScreenProps {
  consentText: string;
  consentVersion: string;
  visitType: "FIRST_VISIT" | "RETURNING_VISIT" | null;
  onNext: () => void | Promise<void>;
  onDecline: () => void | Promise<void>;
  language: "en" | "hi";
  isSubmitting?: boolean;
  error?: string | null;
}

export function ConsentScreen({
  consentText,
  consentVersion,
  visitType,
  onNext,
  onDecline,
  language,
  isSubmitting = false,
  error = null,
}: ConsentScreenProps) {
  const isHi = language === "hi";

  const visitLabel =
    visitType === "RETURNING_VISIT"
      ? isHi
        ? "पिछली यात्रा से जारी"
        : "Returning visit"
      : isHi
        ? "पहली यात्रा"
        : "First visit";

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex w-full flex-col items-center justify-center space-y-0 py-12"
    >
      <div className="mb-12 space-y-4 text-center">
        <div className="mb-6 flex justify-center">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-[var(--color-primary-tint)]">
            <ShieldCheck className="h-10 w-10 text-[var(--color-primary-dark)]" />
          </div>
        </div>

        <h2 className="text-4xl font-bold text-[var(--color-text-primary)]">
          {isHi ? "रोगी सहमति" : "Patient Consent"}
        </h2>

        <p className="text-lg font-semibold text-[var(--color-primary-dark)]">
          {visitLabel}
        </p>

        <p className="mx-auto max-w-2xl text-xl text-[var(--color-text-secondary)]">
          {isHi
            ? "कृपया नीचे दी गई सहमति जानकारी की समीक्षा करें।"
            : "Please review the consent information below before continuing."}
        </p>
      </div>

      <div className="mb-12 w-full max-w-3xl rounded-2xl border-2 border-[var(--color-border)] bg-[var(--color-surface)] p-8 shadow-sm">
        <div className="flex items-start gap-4">
          <FileText className="mt-1 h-6 w-6 flex-shrink-0 text-[var(--color-text-secondary)]" />

          <div className="space-y-6 text-lg text-[var(--color-text-primary)]">
            <p className="leading-relaxed">{consentText}</p>

            <div className="border-t border-[var(--color-border)] pt-4 text-sm text-[var(--color-text-secondary)]">
              {isHi
                ? `सहमति संस्करण: ${consentVersion}`
                : `Consent version: ${consentVersion}`}
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-6 rounded-xl border-2 border-[var(--color-danger)] bg-[var(--color-surface)] px-6 py-3 text-center text-sm font-semibold text-[var(--color-danger)]">
          {error}
        </div>
      )}

      <div className="flex gap-6">
        <Button
          disabled={isSubmitting}
          onClick={() => {
            void onDecline();
          }}
          className="min-w-[200px] rounded-xl border-2 border-[var(--color-danger)] bg-transparent px-10 py-6 text-xl text-[var(--color-danger)] transition-all hover:bg-[var(--color-danger)] hover:text-white"
        >
          {isHi ? "अस्वीकार करें" : "Decline"}
        </Button>

        <Button
          disabled={isSubmitting}
          onClick={() => {
            void onNext();
          }}
          className="min-w-[280px] rounded-xl bg-[var(--color-primary-dark)] px-12 py-6 text-xl text-white shadow-lg transition-all hover:bg-[var(--color-text-primary)]"
        >
          {isSubmitting
            ? isHi
              ? "सहेजा जा रहा है..."
              : "Saving..."
            : isHi
              ? "मैं सहमत हूं"
              : "I Consent"}
        </Button>
      </div>
    </motion.div>
  );
}
