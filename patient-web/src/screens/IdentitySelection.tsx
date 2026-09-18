import { useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Fingerprint, User } from "lucide-react";

interface IdentitySelectionProps {
  onNext: (
    identityType: "abha" | "aadhaar",
    number: string,
  ) => void | Promise<void>;
  language: "en" | "hi";
  isVerifying?: boolean;
  error?: string | null;
}

export function IdentitySelection({
  onNext,
  language,
  isVerifying = false,
  error = null,
}: IdentitySelectionProps) {
  const isHi = language === "hi";
  const [selectedId, setSelectedId] = useState<"abha" | "aadhaar" | null>(null);
  const [showInput, setShowInput] = useState(false);
  const [idNumber, setIdNumber] = useState("");
  const [useBiometric, setUseBiometric] = useState(false);

  const handleIdSelect = (type: "abha" | "aadhaar") => {
    setSelectedId(type);
    setShowInput(true);
  };

  const handleContinue = async () => {
    const requiredLength = selectedId === "abha" ? 14 : 12;

    if (
      selectedId &&
      (idNumber.length >= requiredLength || useBiometric) &&
      !isVerifying
    ) {
      await onNext(selectedId, idNumber);
    }
  };

  const handleBack = () => {
    if (isVerifying) {
      return;
    }

    setShowInput(false);
    setSelectedId(null);
    setIdNumber("");
    setUseBiometric(false);
  };

  const handleNumberInput = (num: string) => {
    if (isVerifying) {
      return;
    }

    const maxLength = selectedId === "abha" ? 14 : 12;

    if (idNumber.length < maxLength) {
      setIdNumber(idNumber + num);
    }
  };

  const handleDelete = () => {
    if (!isVerifying) {
      setIdNumber(idNumber.slice(0, -1));
    }
  };

  const handleClear = () => {
    if (!isVerifying) {
      setIdNumber("");
    }
  };

  if (showInput) {
    const maxLength = selectedId === "abha" ? 14 : 12;
    const displayNumber = idNumber.replace(/(\d{4})(?=\d)/g, "$1 ");

    return (
      <div className="flex h-screen w-full flex-col items-center justify-center overflow-hidden bg-[var(--color-bg)]">
        <button
          className="absolute left-8 top-8 rounded-full p-2 transition-colors hover:bg-[var(--color-surface-alt)]"
          disabled={isVerifying}
          onClick={handleBack}
          type="button"
        >
          <ArrowLeft className="h-6 w-6 text-[var(--color-text-secondary)]" />
        </button>

        <div className="mb-8 space-y-2 text-center">
          <h2 className="text-4xl font-bold text-[var(--color-text-primary)]">
            {isHi
              ? `${selectedId === "abha" ? "ABHA" : "आधार"} नंबर दर्ज करें`
              : `Enter ${selectedId === "abha" ? "ABHA" : "Aadhaar"} Number`}
          </h2>

          <p className="text-lg text-[var(--color-text-secondary)]">
            {selectedId === "abha"
              ? isHi
                ? "14-अंकीय ABHA नंबर"
                : "14-digit ABHA number"
              : isHi
                ? "12-अंकीय आधार नंबर"
                : "12-digit Aadhaar number"}
          </p>
        </div>

        <div className="mb-8 w-full max-w-xl rounded-2xl border-2 border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-lg">
          <div className="flex min-h-[70px] items-center justify-center text-center font-mono text-4xl font-bold tracking-widest text-[var(--color-text-primary)]">
            {displayNumber || (
              <span className="text-[var(--color-border)]">
                _ _ _ _ _ _ _ _ _ _ _ _ _ _
              </span>
            )}
          </div>
        </div>

        <div className="mb-6 grid grid-cols-3 gap-3">
          {["1", "2", "3", "4", "5", "6", "7", "8", "9"].map((num) => (
            <motion.button
              key={num}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="h-16 w-24 rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-surface)] text-2xl font-bold text-[var(--color-text-primary)] shadow-md transition-all hover:border-[var(--color-primary)] hover:bg-[var(--color-primary-tint)]"
              disabled={isVerifying}
              onClick={() => handleNumberInput(num)}
              type="button"
            >
              {num}
            </motion.button>
          ))}

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="h-16 w-24 rounded-xl border-2 border-[var(--color-danger)] bg-[var(--color-surface)] text-base font-semibold text-[var(--color-danger)] shadow-md transition-all hover:bg-[var(--color-danger)] hover:text-white"
            disabled={isVerifying}
            onClick={handleClear}
            type="button"
          >
            Clear
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="h-16 w-24 rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-surface)] text-2xl font-bold text-[var(--color-text-primary)] shadow-md transition-all hover:border-[var(--color-primary)] hover:bg-[var(--color-primary-tint)]"
            disabled={isVerifying}
            onClick={() => handleNumberInput("0")}
            type="button"
          >
            0
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="h-16 w-24 rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-surface)] text-xl font-semibold text-[var(--color-text-secondary)] shadow-md transition-all hover:bg-[var(--color-warning)] hover:text-white"
            disabled={isVerifying}
            onClick={handleDelete}
            type="button"
          >
            ←
          </motion.button>
        </div>

        {error && (
          <div className="mb-5 rounded-xl border-2 border-[var(--color-danger)] bg-[var(--color-surface)] px-6 py-3 text-center text-sm font-semibold text-[var(--color-danger)]">
            {error}
          </div>
        )}

        <div className="flex gap-4">
          <Button
            className={`rounded-xl px-6 py-4 text-lg transition-all ${
              useBiometric
                ? "bg-[var(--color-primary)] text-white shadow-lg"
                : "border-2 border-[var(--color-border)] bg-transparent text-[var(--color-text-secondary)]"
            }`}
            disabled={isVerifying}
            onClick={() => setUseBiometric(!useBiometric)}
          >
            <Fingerprint className="mr-2 inline h-5 w-5" />
            {isHi ? "बायोमेट्रिक" : "Biometric"}
          </Button>

          <Button
            className="rounded-xl bg-[var(--color-primary-dark)] px-8 py-4 text-lg text-white shadow-lg transition-all hover:bg-[var(--color-text-primary)]"
            disabled={
              isVerifying || (idNumber.length < maxLength && !useBiometric)
            }
            onClick={handleContinue}
          >
            {isVerifying
              ? isHi
                ? "सत्यापन..."
                : "Verifying..."
              : isHi
                ? "जारी रखें"
                : "Continue"}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen w-full flex-col items-center justify-center overflow-hidden">
      <div className="mb-12 space-y-4 text-center">
        <h2 className="text-4xl font-bold text-[var(--color-text-primary)]">
          {isHi ? "पहचान का तरीका चुनें" : "Select Identification Method"}
        </h2>

        <p className="text-xl text-[var(--color-text-secondary)]">
          {isHi
            ? "आप अपनी पहचान कैसे दर्ज करना चाहेंगे?"
            : "How would you like to identify yourself?"}
        </p>
      </div>

      <div className="grid w-full max-w-4xl grid-cols-1 gap-8 px-4 md:grid-cols-2">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className={`flex h-64 flex-col items-center justify-center gap-6 rounded-2xl border-2 transition-all duration-200 ${
            selectedId === "abha"
              ? "border-[var(--color-primary)] bg-[var(--color-primary-tint)] shadow-lg"
              : "border-[var(--color-border)] bg-[var(--color-surface)] hover:border-[var(--color-primary)]"
          }`}
          onClick={() => handleIdSelect("abha")}
          type="button"
        >
          <User
            className={`h-16 w-16 ${
              selectedId === "abha"
                ? "text-[var(--color-primary-dark)]"
                : "text-[var(--color-text-secondary)]"
            }`}
          />

          <div className="text-3xl font-semibold text-[var(--color-text-primary)]">
            ABHA
          </div>

          <div className="text-lg text-[var(--color-text-secondary)]">
            {isHi ? "14-अंकीय ABHA नंबर" : "14-digit ABHA Number"}
          </div>
        </motion.button>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className={`flex h-64 flex-col items-center justify-center gap-6 rounded-2xl border-2 transition-all duration-200 ${
            selectedId === "aadhaar"
              ? "border-[var(--color-primary)] bg-[var(--color-primary-tint)] shadow-lg"
              : "border-[var(--color-border)] bg-[var(--color-surface)] hover:border-[var(--color-primary)]"
          }`}
          onClick={() => handleIdSelect("aadhaar")}
          type="button"
        >
          <Fingerprint
            className={`h-16 w-16 ${
              selectedId === "aadhaar"
                ? "text-[var(--color-primary-dark)]"
                : "text-[var(--color-text-secondary)]"
            }`}
          />

          <div className="text-3xl font-semibold text-[var(--color-text-primary)]">
            {isHi ? "आधार" : "Aadhaar"}
          </div>

          <div className="text-lg text-[var(--color-text-secondary)]">
            {isHi ? "12-अंकीय आधार / बायोमेट्रिक" : "12-digit Aadhaar / Biometric"}
          </div>
        </motion.button>
      </div>
    </div>
  );
}
