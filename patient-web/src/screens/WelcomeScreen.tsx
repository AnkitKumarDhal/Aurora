import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Flower2 } from "lucide-react";

interface WelcomeScreenProps {
  onNext: () => void;
  language: "en" | "hi";
}

export function WelcomeScreen({ onNext, language }: WelcomeScreenProps) {
  const isHindi = language === "hi";

  return (
    <div className="relative flex flex-col items-center justify-center w-full py-12">
      {/* Background Logo */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none select-none">
        <div className="flex flex-col items-center opacity-[0.04] dark:opacity-[0.03] transform scale-[2.5]">
          <Flower2
            className="w-48 h-48 text-primary"
            strokeWidth={1}
          />
          <span className="text-[10rem] font-bold text-text-primary tracking-tighter mt-[-2rem]">
            Aurora
          </span>
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="relative z-10 text-center space-y-8 max-w-3xl px-4"
      >
        <div className="space-y-4">
          <h1 className="text-5xl font-bold text-text-primary">
            {isHindi ? "औरोरा में आपका स्वागत है" : "Welcome to Aurora"}
          </h1>
          <p className="text-2xl text-text-secondary font-medium">
            {isHindi
              ? "आपका चिकित्सा इतिहास, हमेशा आपके साथ।"
              : "Your Medical History, Always With You."}
          </p>
        </div>

        <div className="pt-8">
          <Button
            onClick={onNext}
            className="px-12 py-6 text-xl rounded-xl bg-primary-dark hover:bg-text-primary text-white transition-all shadow-lg min-w-[280px]"
          >
            {isHindi ? "शुरू करें" : "Get Started"}
          </Button>
        </div>
      </motion.div>
    </div>
  );
}
