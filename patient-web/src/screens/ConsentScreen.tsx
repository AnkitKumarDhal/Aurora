import { motion } from "framer-motion";
import { FileText, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ConsentScreenProps {
  consentText: string;
  consentVersion: string;
  onNext: () => void | Promise<void>;
  onDecline: () => void | Promise<void>;
  language: "en" | "hi";
  isSubmitting?: boolean;
  error?: string | null;
}

export function ConsentScreen({
  consentText,
  consentVersion,
  onNext,
  onDecline,
  language,
  isSubmitting = false,
  error = null,
}: ConsentScreenProps) {
  const isHi = language === "hi";

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex w-full flex-col items-center justify-center space-y-0 py-12"
    >
      <div className="mb-12 space-y-4 text-center">
        <div className="mb-6 flex justify-center">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-primary-tint">
            <ShieldCheck className="h-10 w-10 text-primary-dark" />
          </div>
        </div>

        <h2 className="text-4xl font-bold text-text-primary">
          {isHi ? "रोगी सहमति" : "Patient Consent"}
        </h2>

        <p className="mx-auto max-w-2xl text-xl text-text-secondary">
          {isHi
            ? "कृपया नीचे दी गई सहमति जानकारी की समीक्षा करें।"
            : "Please review the consent information below before continuing."}
        </p>
      </div>

      <div className="mb-12 w-full max-w-3xl rounded-2xl border-2 border-border bg-surface p-8 shadow-sm">
        <div className="flex items-start gap-4">
          <FileText className="mt-1 h-6 w-6 flex-shrink-0 text-text-secondary" />

          <div className="space-y-6 text-lg text-text-primary">
            <p className="leading-relaxed">{consentText}</p>

            <div className="border-t border-border pt-4 text-sm text-text-secondary">
              {isHi
                ? `सहमति संस्करण: ${consentVersion}`
                : `Consent version: ${consentVersion}`}
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-6 rounded-xl border-2 border-danger bg-surface px-6 py-3 text-center text-sm font-semibold text-danger">
          {error}
        </div>
      )}

      <div className="flex gap-6">
        <Button
          disabled={isSubmitting}
          onClick={() => {
            void onDecline();
          }}
          className="min-w-[200px] rounded-xl border-2 border-danger bg-transparent px-10 py-6 text-xl text-danger transition-all hover:bg-danger hover:text-white"
        >
          {isHi ? "अस्वीकार करें" : "Decline"}
        </Button>

        <Button
          disabled={isSubmitting}
          onClick={() => {
            void onNext();
          }}
          className="min-w-[280px] rounded-xl bg-primary-dark px-12 py-6 text-xl text-white shadow-lg transition-all hover:bg-text-primary"
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
