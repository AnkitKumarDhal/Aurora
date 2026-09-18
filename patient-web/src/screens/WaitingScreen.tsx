import { RotateCcw } from "lucide-react";
import { motion } from "framer-motion";
import { CheckCircle, Sparkles, Star } from "lucide-react";
import { Button } from "@/components/ui/button";

const RESET_SECONDS = 90;

interface WaitingScreenProps {
  onReset: () => void | Promise<void>;
  language: "en" | "hi";
  timeLeft: number;
}

export function WaitingScreen({
  onReset,
  language,
  timeLeft,
}: WaitingScreenProps) {
  const isHi = language === "hi";

  const radius = 50;
  const circumference = 2 * Math.PI * radius;

  const strokeDashoffset =
    circumference - (timeLeft / RESET_SECONDS) * circumference;

  return (
    <div className="relative flex min-h-[80vh] w-full flex-col items-center justify-center overflow-hidden px-4">
      <div className="pointer-events-none absolute inset-0">
        {[...Array(12)].map((_, index) => (
          <motion.div
            key={index}
            className="absolute"
            style={{
              left: "50%",
              top: "30%",
            }}
            initial={{ opacity: 1, scale: 0, x: 0, y: 0 }}
            animate={{
              opacity: [0, 1, 0],
              scale: [0, 1.5, 0],
              x: Math.cos((index * 30 * Math.PI) / 180) * 150,
              y: Math.sin((index * 30 * Math.PI) / 180) * 150,
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              repeatDelay: 3,
              delay: index * 0.1,
            }}
          >
            <Star className="h-6 w-6 fill-[var(--color-warning)] text-[var(--color-warning)]" />
          </motion.div>
        ))}
      </div>

      <motion.div
        initial={{ scale: 0, rotate: -180 }}
        animate={{ scale: 1, rotate: 0 }}
        transition={{
          type: "spring",
          stiffness: 200,
          damping: 15,
        }}
        className="relative mb-6"
      >
        <div className="flex h-32 w-32 items-center justify-center rounded-full bg-gradient-to-br from-[var(--color-success)] to-emerald-600 shadow-2xl">
          <CheckCircle className="h-20 w-20 text-white" strokeWidth={3} />
        </div>

        <motion.div
          className="absolute -right-2 -top-2"
          animate={{ rotate: 360 }}
          transition={{
            duration: 3,
            repeat: Infinity,
            ease: "linear",
          }}
        >
          <Sparkles className="h-8 w-8 text-[var(--color-warning)]" />
        </motion.div>
      </motion.div>

      <motion.h2
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="mb-4 text-center text-4xl font-bold text-[var(--color-text-primary)]"
      >
        {isHi ? "पंजीकरण पूरा हो गया है" : "Registration complete"}
      </motion.h2>

      <motion.p
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="mb-8 max-w-3xl text-center text-xl leading-relaxed text-[var(--color-text-secondary)]"
      >
        {isHi
          ? "कृपया ओपीडी में प्रतीक्षा करें। एक स्टाफ सदस्य आपका नाम पुकारेगा और आपको अगले चरण के लिए मार्गदर्शन करेगा।"
          : "Please wait in the OPD. A staff member will call your name and guide you through the next process."}
      </motion.p>

      <div className="relative mb-6 flex items-center justify-center">
        <svg className="h-32 w-32 -rotate-90 transform">
          <circle
            cx="64"
            cy="64"
            r={radius}
            stroke="var(--color-border)"
            strokeWidth="8"
            fill="transparent"
          />

          <circle
            cx="64"
            cy="64"
            r={radius}
            stroke="var(--color-primary)"
            strokeWidth="8"
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-linear"
          />
        </svg>

        <div className="absolute font-mono text-3xl font-bold text-[var(--color-text-primary)]">
          {timeLeft}s
        </div>
      </div>

      <p className="mb-6 text-lg text-[var(--color-text-secondary)]">
        {isHi
          ? `कियोस्क ${timeLeft} सेकंड में अगले रोगी के लिए रीसेट होगा`
          : `This kiosk will reset for the next patient in ${timeLeft} seconds`}
      </p>

      <Button
        onClick={() => {
          void onReset();
        }}
        className="flex min-w-[280px] items-center gap-3 rounded-xl bg-[var(--color-primary-dark)] px-12 py-6 text-xl text-white shadow-lg transition-all hover:bg-[var(--color-text-primary)]"
      >
        <RotateCcw className="h-6 w-6" />
        {isHi ? "अभी रीसेट करें" : "Reset for Next Patient"}
      </Button>
    </div>
  );
}
