import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { useAdminStore } from "@/store/adminStore";

const TOTAL = 43;
const CIRCUMFERENCE = 2 * Math.PI * 17;

export function PromotionPanel() {
  const promotionState = useAdminStore((state) => state.promotionState);
  const resolvePromotion = useAdminStore((state) => state.resolvePromotion);
  const clearPromotion = useAdminStore((state) => state.clearPromotion);

  const [remaining, setRemaining] = useState(TOTAL);

  useEffect(() => {
    if (promotionState !== "active") {
      return;
    }

    const timer = window.setInterval(() => {
      setRemaining((value) => {
        if (value <= 1) {
          resolvePromotion("auto");
          return 0;
        }

        return value - 1;
      });
    }, 1000);

    return () => window.clearInterval(timer);
  }, [promotionState, resolvePromotion]);

  useEffect(() => {
    if (
      promotionState !== "accepted" &&
      promotionState !== "denied" &&
      promotionState !== "auto"
    ) {
      return;
    }

    const timer = window.setTimeout(() => {
      clearPromotion();
      setRemaining(TOTAL);
    }, 3500);

    return () => window.clearTimeout(timer);
  }, [promotionState, clearPromotion]);

  const mm = String(Math.floor(remaining / 60)).padStart(2, "0");
  const ss = String(remaining % 60).padStart(2, "0");
  const offset = CIRCUMFERENCE * (1 - remaining / TOTAL);

  const ringClass = remaining <= 10 ? "danger" : remaining <= 20 ? "warn" : "";

  return (
    <div className="panel promotion">
      <div className="panel-title">Promotion</div>

      <div id="promoContainer">
        {promotionState === "active" && (
          <div className="promo-card">
            <div className="promo-header">
              <div className="promo-icon" />
              <div className="promo-title">Priority Promotion</div>
            </div>

            <div className="promo-patient">Patient A102</div>

            <div className="promo-meta">High severity · Waiting 31 min</div>

            <div className="promo-desc">
              This patient qualifies for queue promotion.
            </div>

            <div className="countdown-wrap">
              <div className={cn("countdown-ring", ringClass)}>
                <svg width="40" height="40" viewBox="0 0 40 40">
                  <circle className="track" cx="20" cy="20" r="17" />
                  <circle
                    className="progress"
                    cx="20"
                    cy="20"
                    r="17"
                    strokeDasharray="106.81"
                    strokeDashoffset={offset}
                  />
                </svg>
              </div>

              <div>
                <div className="countdown-time">
                  {mm}:{ss}
                </div>
                <div className="countdown-label">Remaining</div>
              </div>
            </div>

            <div className="promo-actions">
              <button
                className="btn btn-accept"
                type="button"
                onClick={() => resolvePromotion("accepted")}
              >
                Accept
              </button>
              <button
                className="btn btn-deny"
                type="button"
                onClick={() => resolvePromotion("denied")}
              >
                Deny
              </button>
            </div>
          </div>
        )}

        {promotionState === "accepted" && (
          <div className="promo-resolved accepted">
            ✓ PROMOTION ACCEPTED · Patient A102 → Priority lane
          </div>
        )}

        {promotionState === "denied" && (
          <div className="promo-resolved denied">
            ✗ PROMOTION DENIED · Patient A102 remains in current lane
          </div>
        )}

        {promotionState === "auto" && (
          <div className="promo-resolved auto">
            ⏱ AUTO-PROMOTED · Patient A102 → Priority lane (no response)
          </div>
        )}

        {promotionState === "empty" && (
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
              Listening for events…
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
