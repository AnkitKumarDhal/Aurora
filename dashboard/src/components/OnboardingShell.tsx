import type { ReactNode } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

const STEP_COUNT = 4;

export function OnboardingShell({
  step,
  onBack,
  onNext,
  nextDisabled = false,
  children,
}: {
  step: number; // 0..3
  onBack?: () => void;
  onNext?: () => void;
  nextDisabled?: boolean;
  children: ReactNode;
}) {
  return (
    <div className="min-h-screen bg-background flex flex-col items-center px-4 py-6">
      <div className="w-full max-w-sm flex-1 flex flex-col">
        <div className="flex items-center justify-between mb-8">
          {onBack ? (
            <button
              onClick={onBack}
              className="size-10 rounded-full bg-muted text-primary flex items-center justify-center"
              aria-label="Back"
            >
              <ChevronLeft className="size-5" />
            </button>
          ) : (
            <div className="size-10" />
          )}

          <div className="flex items-center gap-1.5">
            {Array.from({ length: STEP_COUNT }).map((_, i) => (
              <span
                key={i}
                className={
                  i === step
                    ? "h-2 w-6 rounded-full bg-accent"
                    : "h-2 w-2 rounded-full bg-border"
                }
              />
            ))}
          </div>

          <div className="size-10" />
        </div>

        <div className="flex-1">{children}</div>

        {onNext && (
          <div className="flex justify-end mt-6">
            <button
              onClick={onNext}
              disabled={nextDisabled}
              className="size-14 rounded-full bg-accent text-accent-foreground flex items-center justify-center shadow-lg shadow-accent/30 disabled:opacity-40 disabled:shadow-none"
              aria-label="Next"
            >
              <ChevronRight className="size-6" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
