import { useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Delete, Fingerprint, ShieldCheck, User } from "lucide-react";
import { PatientBackButton } from "@/components/PatientBackButton";

interface IdentitySelectionProps {
  onNext: (
    identityType: "abha" | "aadhaar",
    number: string,
  ) => Promise<boolean>;
  onVerifyOtp: (otp: string) => void | Promise<void>;
  onBack: () => void | Promise<void>;
  language: "en" | "hi";
  isVerifying?: boolean;
  error?: string | null;
  otpChallengeId?: string | null;
  otpDemoCode?: string | null;
}

export function IdentitySelection({
  onNext,
  onVerifyOtp,
  onBack,
  language,
  isVerifying = false,
  error = null,
  otpChallengeId = null,
  otpDemoCode = null,
}: IdentitySelectionProps) {
  const isHi = language === "hi";
  const [selectedId, setSelectedId] = useState<"abha" | "aadhaar" | null>(null);
  const [showInput, setShowInput] = useState(false);
  const [showOtp, setShowOtp] = useState(false);
  const [idNumber, setIdNumber] = useState("");
  const [otpNumber, setOtpNumber] = useState("");

  const handleIdSelect = (type: "abha" | "aadhaar") => {
    setSelectedId(type);
    setShowInput(true);
    setShowOtp(false);
    setIdNumber("");
    setOtpNumber("");
  };

  const handleContinue = async () => {
    if (
      !selectedId ||
      idNumber.length !== (selectedId === "abha" ? 14 : 12) ||
      isVerifying
    ) {
      return;
    }

    const success = await onNext(selectedId, idNumber);

    if (!success) {
      return;
    }

    setShowOtp(true);
    setOtpNumber("");
  };

  const handleVerifyOtp = async () => {
    if (otpNumber.length !== 6 || isVerifying || !otpChallengeId) {
      return;
    }

    await onVerifyOtp(otpNumber);
  };

  const handleBack = () => {
    if (isVerifying) {
      return;
    }

    if (showOtp) {
      setShowOtp(false);
      setOtpNumber("");
      return;
    }

    if (showInput) {
      setShowInput(false);
      setSelectedId(null);
      setIdNumber("");
      return;
    }

    void onBack();
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

  const handleOtpInput = (num: string) => {
    if (!isVerifying && otpNumber.length < 6) {
      setOtpNumber(otpNumber + num);
    }
  };

  const handleOtpDelete = () => {
    if (!isVerifying) {
      setOtpNumber(otpNumber.slice(0, -1));
    }
  };

  const displayNumber = idNumber.replace(/(\d{4})(?=\d)/g, "$1 ");

  const displayOtp = otpNumber
    .split("")
    .map(() => "•")
    .join(" ");

  if (showOtp && otpChallengeId) {
    return (
      <div className="relative flex h-[calc(100svh-8rem)] w-full flex-col items-center justify-center overflow-hidden bg-bg md:h-[calc(100svh-11rem)]">
        <PatientBackButton
          className="absolute left-0 top-0 z-20"
          disabled={isVerifying}
          language={language}
          onClick={handleBack}
        />

        <div className="mb-4 space-y-2 text-center">
          <div className="mb-2 flex justify-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary-tint">
              <ShieldCheck className="h-8 w-8 text-primary-dark" />
            </div>
          </div>

          <h2 className="text-3xl font-bold text-text-primary">
            {isHi ? "OTP सत्यापन" : "OTP Verification"}
          </h2>

          <p className="text-base text-text-secondary">
            {isHi
              ? "आपके पंजीकृत मोबाइल नंबर पर एक OTP भेजा गया है।"
              : "A one-time password has been sent to your registered mobile number."}
          </p>
        </div>

        {otpDemoCode && (
          <div className="mb-4 rounded-xl border-2 border-primary bg-primary-tint px-5 py-2.5 text-center">
            <div className="text-sm font-semibold text-text-secondary">
              {isHi ? "डेमो OTP" : "Demo OTP"}
            </div>

            <div className="mt-1 font-mono text-2xl font-bold tracking-widest text-primary-dark">
              {otpDemoCode}
            </div>
          </div>
        )}

        <div className="mb-4 w-full max-w-lg rounded-2xl border-2 border-border bg-surface p-4 shadow-lg">
          <div className="flex min-h-[60px] items-center justify-center text-center font-mono text-3xl font-bold tracking-widest text-text-primary">
            {displayOtp || (
              <span className="text-border">• • • • • •</span>
            )}
          </div>
        </div>

        <div className="mb-4 grid grid-cols-3 gap-2">
          {["1", "2", "3", "4", "5", "6", "7", "8", "9"].map((num) => (
            <Button
              key={num}
              type="button"
              variant="outline"
              className="h-14 w-20 rounded-xl border-2 border-border bg-surface text-2xl font-bold text-text-primary shadow-md transition-all hover:border-primary hover:bg-primary-tint active:scale-[0.95]"
              disabled={isVerifying}
              onClick={() => handleOtpInput(num)}
            >
              {num}
            </Button>
          ))}

          <Button
            type="button"
            variant="outline"
            className="h-14 w-20 rounded-xl border-2 border-danger bg-surface text-base font-semibold text-danger shadow-md transition-all hover:bg-danger hover:text-white active:scale-[0.95]"
            disabled={isVerifying}
            onClick={handleOtpDelete}
          >
            <Delete className="mx-auto h-5 w-5" />
          </Button>

          <Button
            type="button"
            variant="outline"
            className="h-14 w-20 rounded-xl border-2 border-border bg-surface text-2xl font-bold text-text-primary shadow-md transition-all hover:border-primary hover:bg-primary-tint active:scale-[0.95]"
            disabled={isVerifying}
            onClick={() => handleOtpInput("0")}
          >
            0
          </Button>

          <Button
            type="button"
            variant="outline"
            className="h-14 w-20 rounded-xl border-2 border-border bg-surface text-lg font-semibold text-text-secondary shadow-md transition-all hover:bg-warning hover:text-white active:scale-[0.95]"
            disabled={isVerifying}
            onClick={() => setOtpNumber("")}
          >
            Clear
          </Button>
        </div>

        {error && (
          <div className="mb-3 rounded-xl border-2 border-danger bg-surface px-5 py-2.5 text-center text-sm font-semibold text-danger">
            {error}
          </div>
        )}

        <Button
          type="button"
          className="rounded-xl bg-primary-dark px-7 py-3 text-base text-white shadow-lg transition-all hover:bg-text-primary active:scale-[0.98]"
          disabled={isVerifying || otpNumber.length !== 6}
          onClick={() => {
            void handleVerifyOtp();
          }}
        >
          {isVerifying
            ? isHi
              ? "सत्यापन..."
              : "Verifying..."
            : isHi
              ? "OTP सत्यापित करें"
              : "Verify OTP"}
        </Button>
      </div>
    );
  }

  if (showInput && selectedId) {
    const maxLength = selectedId === "abha" ? 14 : 12;

    return (
      <div className="relative flex h-[calc(100svh-8rem)] w-full flex-col items-center justify-center overflow-hidden bg-bg md:h-[calc(100svh-11rem)]">
        <PatientBackButton
          className="absolute left-0 top-0 z-20"
          disabled={isVerifying}
          language={language}
          onClick={handleBack}
        />

        <div className="mb-8 space-y-2 text-center">
          <h2 className="text-4xl font-bold text-text-primary">
            {isHi
              ? `${selectedId === "abha" ? "ABHA" : "आधार"} नंबर दर्ज करें`
              : `Enter ${selectedId === "abha" ? "ABHA" : "Aadhaar"} Number`}
          </h2>

          <p className="text-lg text-text-secondary">
            {selectedId === "abha"
              ? isHi
                ? "14-अंकीय ABHA नंबर"
                : "14-digit ABHA number"
              : isHi
                ? "12-अंकीय आधार नंबर"
                : "12-digit Aadhaar number"}
          </p>
        </div>

        <div className="mb-8 w-full max-w-xl rounded-2xl border-2 border-border bg-surface p-6 shadow-lg">
          <div className="flex min-h-[70px] items-center justify-center text-center font-mono text-4xl font-bold tracking-widest text-text-primary">
            {displayNumber || (
              <span className="text-border">
                _ _ _ _ _ _ _ _ _ _ _ _ _ _
              </span>
            )}
          </div>
        </div>

        <div className="mb-6 grid grid-cols-3 gap-3">
          {["1", "2", "3", "4", "5", "6", "7", "8", "9"].map((num) => (
            <Button
              key={num}
              type="button"
              variant="outline"
              className="h-16 w-24 rounded-xl border-2 border-border bg-surface text-2xl font-bold text-text-primary shadow-md transition-all hover:border-primary hover:bg-primary-tint active:scale-[0.95]"
              disabled={isVerifying}
              onClick={() => handleNumberInput(num)}
            >
              {num}
            </Button>
          ))}

          <Button
            type="button"
            variant="outline"
            className="h-16 w-24 rounded-xl border-2 border-danger bg-surface text-base font-semibold text-danger shadow-md transition-all hover:bg-danger hover:text-white active:scale-[0.95]"
            disabled={isVerifying}
            onClick={handleClear}
          >
            Clear
          </Button>

          <Button
            type="button"
            variant="outline"
            className="h-16 w-24 rounded-xl border-2 border-border bg-surface text-2xl font-bold text-text-primary shadow-md transition-all hover:border-primary hover:bg-primary-tint active:scale-[0.95]"
            disabled={isVerifying}
            onClick={() => handleNumberInput("0")}
          >
            0
          </Button>

          <Button
            type="button"
            variant="outline"
            className="h-16 w-24 rounded-xl border-2 border-border bg-surface text-2xl font-bold text-text-secondary shadow-md transition-all hover:bg-warning hover:text-white active:scale-[0.95]"
            disabled={isVerifying}
            onClick={handleDelete}
          >
            ←
          </Button>
        </div>

        {error && (
          <div className="mb-5 rounded-xl border-2 border-danger bg-surface px-6 py-3 text-center text-sm font-semibold text-danger">
            {error}
          </div>
        )}

        <Button
          type="button"
          className="rounded-xl bg-primary-dark px-8 py-4 text-lg text-white shadow-lg transition-all hover:bg-text-primary active:scale-[0.98]"
          disabled={isVerifying || idNumber.length !== maxLength}
          onClick={() => {
            void handleContinue();
          }}
        >
          {isVerifying
            ? isHi
              ? "OTP भेजा जा रहा है..."
              : "Sending OTP..."
            : isHi
              ? "जारी रखें"
              : "Continue"}
        </Button>
      </div>
    );
  }

  return (
    <div className="relative flex h-[calc(100svh-8rem)] w-full flex-col items-center justify-center overflow-hidden bg-bg md:h-[calc(100svh-11rem)]">
      <PatientBackButton
        className="absolute left-0 top-0 z-20"
        disabled={isVerifying}
        language={language}
        onClick={onBack}
      />

      <div className="mb-12 space-y-4 text-center">
        <h2 className="text-4xl font-bold text-text-primary">
          {isHi ? "पहचान का तरीका चुनें" : "Select Identification Method"}
        </h2>

        <p className="text-xl text-text-secondary">
          {isHi
            ? "आप अपनी पहचान कैसे दर्ज करना चाहेंगे?"
            : "How would you like to identify yourself?"}
        </p>
      </div>

      <div className="grid w-full max-w-4xl grid-cols-1 gap-8 px-4 md:grid-cols-2">
        <Button
          type="button"
          variant="outline"
          className={`flex h-64 w-full flex-col items-center justify-center gap-6 rounded-2xl border-2 text-text-primary transition-all duration-200 active:scale-[0.98] ${
            selectedId === "abha"
              ? "border-primary bg-primary-tint shadow-lg"
              : "border-border bg-surface hover:border-primary hover:bg-primary-tint"
          }`}
          onClick={() => handleIdSelect("abha")}
        >
          <User
            className={`h-16 w-16 ${
              selectedId === "abha"
                ? "text-primary-dark"
                : "text-text-secondary"
            }`}
          />

          <div className="text-3xl font-semibold text-text-primary">
            ABHA
          </div>

          <div className="text-lg text-text-secondary">
            {isHi ? "14-अंकीय ABHA नंबर" : "14-digit ABHA Number"}
          </div>
        </Button>

        <Button
          type="button"
          variant="outline"
          className={`flex h-64 w-full flex-col items-center justify-center gap-6 rounded-2xl border-2 text-text-primary transition-all duration-200 active:scale-[0.98] ${
            selectedId === "aadhaar"
              ? "border-primary bg-primary-tint shadow-lg"
              : "border-border bg-surface hover:border-primary hover:bg-primary-tint"
          }`}
          onClick={() => handleIdSelect("aadhaar")}
        >
          <Fingerprint
            className={`h-16 w-16 ${
              selectedId === "aadhaar"
                ? "text-primary-dark"
                : "text-text-secondary"
            }`}
          />

          <div className="text-3xl font-semibold text-text-primary">
            {isHi ? "आधार" : "Aadhaar"}
          </div>

          <div className="text-lg text-text-secondary">
            {isHi ? "12-अंकीय आधार" : "12-digit Aadhaar"}
          </div>
        </Button>
      </div>
    </div>
  );
}
