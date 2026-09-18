import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DoctorCaseResponse } from "@/types/api";
import { getUrgencyStyles } from "@/lib/urgency";
import { formatStatusLabel } from "../utils";

export default function TriagePanel({
  triage,
}: {
  triage: DoctorCaseResponse["triage"];
}) {
  if (!triage) {
    return (
      <Card className="rounded-[20px] border border-border bg-surface p-0 shadow-none">
        <CardHeader className="px-[22px] pb-0 pt-5">
          <CardTitle className="font-display text-[15.5px] font-semibold text-primary-dark">
            Triage
          </CardTitle>
        </CardHeader>

        <CardContent className="px-[22px] pb-5 pt-[14px]">
          <span className="text-xs italic text-text-secondary">
            No triage result available.
          </span>
        </CardContent>
      </Card>
    );
  }

  const severity = getUrgencyStyles(triage.urgency_level);

  return (
    <Card className="rounded-[20px] border border-border bg-surface p-0 shadow-none">
      <CardHeader className="px-[22px] pb-0 pt-5">
        <CardTitle className="font-display text-[15.5px] font-semibold text-primary-dark">
          Triage
        </CardTitle>
      </CardHeader>

      <CardContent className="px-[22px] pb-5 pt-[14px]">
        <div className="flex items-center justify-between border-b border-border py-[9px]">
          <span className="text-[12.5px] font-semibold text-text-secondary">
            Urgency level
          </span>

          <span
            className="rounded-full px-2.5 py-1 text-[12px] font-extrabold"
            style={{
              background: severity.badgeBackground,
              color: severity.badgeColor,
            }}
          >
            Level {triage.urgency_level ?? "—"} · {severity.label}
          </span>
        </div>

        <div className="border-b border-border py-[9px]">
          <div className="flex items-center justify-between">
            <span className="text-[12.5px] font-semibold text-text-secondary">
              Priority score
            </span>

            <span className="text-[13.5px] font-extrabold text-text-primary">
              {triage.priority_score ?? "—"} / 100
            </span>
          </div>

          {triage.priority_score !== null && (
            <div className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-border">
              <div
                className="h-full rounded-full bg-gradient-to-r from-primary to-danger"
                style={{
                  width: `${Math.min(
                    Math.max(triage.priority_score, 0),
                    100,
                  )}%`,
                }}
              />
            </div>
          )}
        </div>

        <div className="flex items-center justify-between border-b border-border py-[9px]">
          <span className="text-[12.5px] font-semibold text-text-secondary">
            Red flags
          </span>

          <span
            className="text-[13.5px] font-extrabold"
            style={{
              color: triage.red_flags_present
                ? "var(--aurora-danger)"
                : "var(--aurora-text-primary)",
            }}
          >
            {triage.red_flags_present ? "Present" : "None detected"}
          </span>
        </div>

        <div className="flex items-center justify-between py-[9px] pb-0">
          <span className="text-[12.5px] font-semibold text-text-secondary">
            Status
          </span>

          <span className="text-[13.5px] font-extrabold text-text-primary">
            {formatStatusLabel(triage.status)}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
