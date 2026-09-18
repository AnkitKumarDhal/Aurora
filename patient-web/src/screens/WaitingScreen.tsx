import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { CheckCircle, UserPlus, Star, Sparkles } from "lucide-react";

interface WaitingScreenProps {
  onReset: () => void;
  language: "en" | "hi";
}

export function WaitingScreen({ onReset, language }: WaitingScreenProps) {
  const isHi = language === "hi";
  const [timeLeft, setTimeLeft] = useState(60);

  useEffect(() => {
    if (timeLeft <= 0) {
      onReset();
      return;
    }
    const timer = setInterval(() => setTimeLeft((prev) => prev - 1), 1000);
    return () => clearInterval(timer);
  }, [timeLeft, onReset]);

  const radius = 50;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (timeLeft / 60) * circumference;

  return (
    <div className="flex flex-col items-center justify-center w-full h-[80vh] relative overflow-hidden">
      {/* Exploding Stars Animation */}
      <div className="absolute inset-0 pointer-events-none">
        {[...Array(12)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute"
            style={{
              left: "50%",
              top: "30%",
            }}
            initial={{ opacity: 1, scale: 0, x: 0, y: 0 }}
            animate={{
              opacity: [0, 1, 0],
              scale: [0, 1.5, 0],
              x: Math.cos((i * 30 * Math.PI) / 180) * 150,
              y: Math.sin((i * 30 * Math.PI) / 180) * 150,
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              repeatDelay: 3,
              delay: i * 0.1,
            }}
          >
            <Star className="h-6 w-6 text-[var(--color-warning)] fill-[var(--color-warning)]" />
          </motion.div>
        ))}
      </div>

      {/* Big Animated Checkmark */}
      <motion.div
        initial={{ scale: 0, rotate: -180 }}
        animate={{ scale: 1, rotate: 0 }}
        transition={{ type: "spring", stiffness: 200, damping: 15 }}
        className="relative mb-6"
      >
        <div className="h-32 w-32 rounded-full bg-gradient-to-br from-[var(--color-success)] to-emerald-600 flex items-center justify-center shadow-2xl">
          <CheckCircle className="h-20 w-20 text-white" strokeWidth={3} />
        </div>
        <motion.div
          className="absolute -top-2 -right-2"
          animate={{ rotate: 360 }}
          transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
        >
          <Sparkles className="h-8 w-8 text-[var(--color-warning)]" />
        </motion.div>
      </motion.div>

      <motion.h2
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="text-4xl font-bold text-[var(--color-text-primary)] mb-3"
      >
        {isHi ? "पंजीकरण पूरा हुआ!" : "Registration Complete!"}
      </motion.h2>

      <motion.p
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="text-xl text-[var(--color-text-secondary)] mb-8 max-w-2xl text-center"
      >
        {isHi
          ? "आपका पंजीकरण पूरा हो गया है। डॉक्टर जल्द ही आपको बुलाएंगे।"
          : "Your registration is complete. The doctor will call you shortly."}
      </motion.p>

      {/* Circular Timer */}
      <div className="relative flex items-center justify-center mb-6">
        <svg className="transform -rotate-90 w-32 h-32">
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
        <div className="absolute text-3xl font-bold text-[var(--color-text-primary)] font-mono">
          {timeLeft}s
        </div>
      </div>

      <p className="text-lg text-[var(--color-text-secondary)] mb-6">
        {isHi
          ? `अगले रोगी के लिए ${timeLeft} सेकंड में रीसेट हो रहा है`
          : `Resetting for next patient in ${timeLeft} seconds`}
      </p>

      <Button
        onClick={onReset}
        className="px-12 py-6 text-xl rounded-xl bg-[var(--color-primary-dark)] hover:bg-[var(--color-text-primary)] text-white transition-all shadow-lg min-w-[280px] flex items-center gap-3"
      >
        <UserPlus className="h-6 w-6" />
        {isHi ? "अगला रोगी" : "Next Patient"}
      </Button>
    </div>
  );
}
