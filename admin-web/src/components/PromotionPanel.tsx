import { useEffect, useState } from "react";

import { approvePromotion, denyPromotion } from "@/api/admin";

import type { AdminPromotion } from "@/types/admin";

interface PromotionPanelProps {
  promotions: AdminPromotion[];
  onResolved: () => Promise<void>;
}

function formatRemaining(deadline: string): {
  totalSeconds: number;
  label: string;
} {
  const remaining = Math.max(
    0,
    Math.ceil((new Date(deadline).getTime() - Date.now()) / 1000),
  );

  const minutes = Math.floor(remaining / 60);

  const seconds = remaining % 60;

  return {
    totalSeconds: remaining,
    label:
      `${String(minutes).padStart(2, "0")}:` +
      `${String(seconds).padStart(2, "0")}`,
  };
}

export function PromotionPanel({
  promotions,
  onResolved,
}: PromotionPanelProps) {
  const promotion = promotions[0] ?? null;

  const [remaining, setRemaining] = useState(
    promotion
      ? formatRemaining(promotion.decisionDeadline)
      : {
          totalSeconds: 0,
          label: "00:00",
        },
  );

  const [isSubmitting, setIsSubmitting] = useState(false);

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!promotion) {
      return;
    }

    const update = () => {
      setRemaining(formatRemaining(promotion.decisionDeadline));
    };

    update();

    const timer = window.setInterval(update, 1000);

    return () => window.clearInterval(timer);
  }, [promotion]);

  async function handleDecision(decision: "approve" | "deny"): Promise<void> {
    if (!promotion || isSubmitting) {
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      if (decision === "approve") {
        await approvePromotion(promotion.promotionRequestId);
      } else {
        await denyPromotion(promotion.promotionRequestId);
      }

      await onResolved();
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "Unable to resolve promotion.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  if (!promotion) {
    return (
      <div className="panel promotion">
        <div className="panel-title">Promotion</div>

        <div
          style={{
            textAlign: "center",
            padding: "20px 10px",
          }}
        >
          <div
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: "11px",
              letterSpacing: "1.5px",
              color: "var(--color-text-secondary)",
              textTransform: "uppercase",
              marginBottom: "8px",
            }}
          >
            No active promotions
          </div>

          <div
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: "11px",
              color: "var(--color-text-secondary)",
              opacity: 0.6,
            }}
          >
            Listening for promotion events…
          </div>
        </div>
      </div>
    );
  }

  const urgent = remaining.totalSeconds <= 10;

  return (
    <div className="panel promotion">
      <div className="panel-title">Promotion</div>

      <div className="promo-card">
        <div className="promo-header">
          <div className="promo-icon" />

          <div className="promo-title">Priority Promotion</div>
        </div>

        <div className="promo-patient">{promotion.patientName}</div>

        <div className="promo-meta">
          {promotion.currentDoctorName ?? "Unassigned"} →{" "}
          {promotion.targetDoctorName}
        </div>

        <div className="promo-desc">{promotion.reason}</div>

        <div className="countdown-wrap">
          <div className={`countdown-ring${urgent ? " danger" : ""}`}>
            <svg width="40" height="40" viewBox="0 0 40 40">
              <circle className="track" cx="20" cy="20" r="17" />

              <circle
                className="progress"
                cx="20"
                cy="20"
                r="17"
                strokeDasharray="106.81"
                strokeDashoffset={106.81 * (1 - remaining.totalSeconds / 60)}
              />
            </svg>
          </div>

          <div>
            <div className="countdown-time">{remaining.label}</div>

            <div className="countdown-label">Remaining</div>
          </div>
        </div>

        {error && <div className="login-error">{error}</div>}

        <div className="promo-actions">
          <button
            className="btn btn-accept"
            type="button"
            disabled={isSubmitting}
            onClick={() => void handleDecision("approve")}
          >
            {isSubmitting ? "Saving..." : "Accept"}
          </button>

          <button
            className="btn btn-deny"
            type="button"
            disabled={isSubmitting}
            onClick={() => void handleDecision("deny")}
          >
            Deny
          </button>
        </div>
      </div>
    </div>
  );
}
