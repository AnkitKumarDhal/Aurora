import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

interface PatientBackButtonProps {
  language: "en" | "hi";
  onClick: () => void | Promise<void>;
  disabled?: boolean;
  className?: string;
}

export function PatientBackButton({
  language,
  onClick,
  disabled = false,
  className = "",
}: PatientBackButtonProps) {
  return (
    <Button
      aria-label={language === "hi" ? "वापस जाएं" : "Go back"}
      className={`rounded-full border-border bg-surface px-5 py-2.5 text-text-primary shadow-sm transition-all hover:bg-surface-alt ${className}`}
      disabled={disabled}
      onClick={() => {
        void onClick();
      }}
      type="button"
      variant="outline"
    >
      <ArrowLeft className="mr-2 h-4 w-4" />
      {language === "hi" ? "वापस" : "Back"}
    </Button>
  );
}
