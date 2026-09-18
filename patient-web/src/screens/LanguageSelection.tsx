import { useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";

interface LanguageSelectionProps {
  onNext: (language: "en" | "hi") => void;
}

export function LanguageSelection({ onNext }: LanguageSelectionProps) {
  const [selectedLang, setSelectedLang] = useState<"en" | "hi" | null>(null);

  const handleContinue = () => {
    if (selectedLang) {
      onNext(selectedLang);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex flex-col items-center justify-center w-full py-12"
    >
      <div className="text-center space-y-4 mb-12">
        <h2 className="text-4xl font-bold text-text-primary">
          Select Your Language
        </h2>
        <p className="text-xl text-text-secondary">
          Choose your preferred language for this session
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-4xl px-4 mb-12">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => setSelectedLang("en")}
          className={`h-64 rounded-2xl border-2 transition-all duration-200 flex flex-col items-center justify-center gap-4 ${
            selectedLang === "en"
              ? "border-primary bg-primary-tint shadow-lg"
              : "border-border bg-surface hover:border-primary"
          }`}
        >
          <div className="text-4xl font-semibold text-text-primary">
            English
          </div>
          <div className="text-xl text-text-secondary">
            Continue in English
          </div>
        </motion.button>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => setSelectedLang("hi")}
          className={`h-64 rounded-2xl border-2 transition-all duration-200 flex flex-col items-center justify-center gap-4 ${
            selectedLang === "hi"
              ? "border-primary bg-primary-tint shadow-lg"
              : "border-border bg-surface hover:border-primary"
          }`}
        >
          <div className="text-4xl font-semibold text-text-primary">
            हिन्दी
          </div>
          <div className="text-xl text-text-secondary">
            हिंदी में जारी रखें
          </div>
        </motion.button>
      </div>

      <Button
        onClick={handleContinue}
        disabled={!selectedLang}
        className="px-12 py-6 text-xl rounded-xl bg-primary-dark hover:bg-text-primary text-white disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-lg min-w-[280px]"
      >
        Continue
      </Button>
    </motion.div>
  );
}
