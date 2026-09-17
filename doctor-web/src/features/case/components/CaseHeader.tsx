import { AlertTriangle, Check, LoaderCircle, Phone, Play } from "lucide-react";
import type { ReactNode } from "react";
import { Button } from "@/components/ui/button";
import type {
  DoctorCaseResponse,
  DoctorQueueEntry,
  SessionStatus,
} from "@/types/api";
import { getUrgencyStyles } from "@/lib/urgency";
import { formatWaitingTime, getInitials } from "../utils";

function workflowIndex(status: SessionStatus): number {
  const statuses: SessionStatus[] = [
    "ASSIGNED",
    "CALLED",
    "IN_CONSULTATION",
    "COMPLETED",
  ];

  const index = statuses.indexOf(status);

  return index < 0 ? 0 : index;
}

function WorkflowStepper({ status }: { status: SessionStatus }) {
  const currentIndex = workflowIndex(status);

  const steps = [
    {
      status: "ASSIGNED" as SessionStatus,
      label: "Assigned",
    },
    {
      status: "CALLED" as SessionStatus,
      label: "Called",
    },
    {
      status: "IN_CONSULTATION" as SessionStatus,
      label: "In consultation",
    },
    {
      status: "COMPLETED" as SessionStatus,
      label: "Completed",
    },
  ];

  return (
    <div className="mt-4.5 flex flex-wrap items-center">
      {steps.map((step, index) => {
        const done = index < currentIndex;
        const current = index === currentIndex;

        return (
          <div className="flex items-center" key={step.status}>
            <div className="flex items-center gap-2">
              <span
                className={[
                  "flex size-5.5 items-center justify-center rounded-full border-2 text-[10px] font-extrabold transition-all duration-300 ease-out",
                  done
                    ? "border-primary-dark bg-primary-dark text-surface"
                    : current
                      ? "border-accent bg-accent text-accent-dark"
                      : "border-border bg-surface text-text-secondary",
                ].join(" ")}
              >
                {done ? <Check className="size-3" /> : index + 1}
              </span>

              <span
                className={[
                  "text-xs font-bold transition-colors duration-300",
                  done || current ? "text-primary-dark" : "text-text-secondary",
                ].join(" ")}
              >
                {step.label}
              </span>
            </div>

            {index < steps.length - 1 && (
              <span
                className={[
                  "mx-1.5 h-0.5 w-7 transition-colors duration-300",
                  index < currentIndex ? "bg-primary-dark" : "bg-border",
                ].join(" ")}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

function WorkflowAction({
  actionKey,
  children,
}: {
  actionKey: string;
  children: ReactNode;
}) {
  return (
    <div
      className="motion-safe:animate-in motion-safe:fade-in-0 motion-safe:slide-in-from-right-2 motion-safe:duration-200"
      key={actionKey}
    >
      {children}
    </div>
  );
}

function WorkflowActions({
  caseData,
  queueEntry,
  isActing,
  onCall,
  onStart,
  onComplete,
}: {
  caseData: DoctorCaseResponse;
  queueEntry: DoctorQueueEntry | null;
  isActing: boolean;
  onCall: () => void;
  onStart: () => void;
  onComplete: () => void;
}) {
  const status = caseData.session.status;
  const summaryConfirmed = caseData.summary?.status === "CONFIRMED";

  if (!queueEntry) {
    return null;
  }

  const actionKey = `${status}:${queueEntry.status}:${summaryConfirmed}`;

  if (status === "ASSIGNED" && queueEntry.status === "PROMOTION_PENDING") {
    return (
      <WorkflowAction actionKey={actionKey}>
        <span
          className="rounded-full px-3 py-2 text-[11px] font-bold"
          style={{
            background:
              "color-mix(in srgb, var(--aurora-warning) 22%, var(--aurora-surface))",
            color:
              "color-mix(in srgb, var(--aurora-warning) 60%, var(--aurora-text-primary))",
          }}
        >
          Promotion review
        </span>
      </WorkflowAction>
    );
  }

  if (status === "ASSIGNED" && queueEntry.status === "WAITING") {
    return (
      <WorkflowAction actionKey={actionKey}>
        <Button
          className="h-9 rounded-md bg-primary-dark px-4 text-xs font-bold text-surface hover:bg-primary-dark/90"
          disabled={isActing}
          onClick={onCall}
          type="button"
        >
          {isActing ? (
            <>
              <LoaderCircle className="size-4 animate-spin" />
              Calling
            </>
          ) : (
            <>
              <Phone className="size-4" />
              Call patient
            </>
          )}
        </Button>
      </WorkflowAction>
    );
  }

  if (status === "CALLED") {
    return (
      <WorkflowAction actionKey={actionKey}>
        <Button
          className="h-9 rounded-md bg-primary-dark px-4 text-xs font-bold text-surface hover:bg-primary-dark/90"
          disabled={isActing}
          onClick={onStart}
          type="button"
        >
          {isActing ? (
            <>
              <LoaderCircle className="size-4 animate-spin" />
              Starting
            </>
          ) : (
            <>
              <Play className="size-4" />
              Start consultation
            </>
          )}
        </Button>
      </WorkflowAction>
    );
  }

  if (status === "IN_CONSULTATION") {
    return (
      <WorkflowAction actionKey={actionKey}>
        <Button
          className="h-9 rounded-md bg-primary-dark px-4 text-xs font-bold text-surface hover:bg-primary-dark/90"
          disabled={isActing || !summaryConfirmed}
          onClick={onComplete}
          type="button"
        >
          {isActing ? (
            <>
              <LoaderCircle className="size-4 animate-spin" />
              Completing
            </>
          ) : (
            <>
              <Check className="size-4" />
              Complete consultation
            </>
          )}
        </Button>
      </WorkflowAction>
    );
  }

  return (
    <WorkflowAction actionKey={actionKey}>
      <span className="rounded-full bg-primary-tint px-3 py-2 text-[11px] font-bold text-text-secondary">
        Consultation completed
      </span>
    </WorkflowAction>
  );
}

export default function CaseHeader({
  caseData,
  queueEntry,
  liveWaitingSeconds,
  isActing,
  onCall,
  onStart,
  onComplete,
}: {
  caseData: DoctorCaseResponse;
  queueEntry: DoctorQueueEntry | null;
  liveWaitingSeconds: number | null;
  isActing: boolean;
  onCall: () => void;
  onStart: () => void;
  onComplete: () => void;
}) {
  const severity = getUrgencyStyles(caseData.triage?.urgency_level ?? null);

  return (
    <div className="rounded-[20px] border border-border bg-surface px-6 py-5.5">
      <div className="flex flex-wrap items-start justify-between gap-5">
        <div className="flex items-center gap-3.5">
          <span className="flex size-13 shrink-0 items-center justify-center rounded-2xl bg-linear-to-br from-primary-tint to-accent-tint font-display text-lg font-semibold text-primary-dark">
            {getInitials(caseData.patient?.display_name ?? "Patient")}
          </span>

          <div>
            <h1 className="font-display text-[21px] font-semibold text-primary-dark">
              {caseData.patient?.display_name ?? "Unknown patient"}
            </h1>

            <div className="mt-0.75 flex flex-wrap items-center gap-2.5 text-[12.5px] text-text-secondary">
              <span>
                {caseData.patient?.age !== null &&
                caseData.patient?.age !== undefined
                  ? `${caseData.patient.age} yrs`
                  : "Age unknown"}
              </span>

              <span>·</span>

              <span
                className="rounded-full px-2.5 py-0.75 text-[10.5px] font-extrabold"
                style={{
                  background: severity.badgeBackground,
                  color: severity.badgeColor,
                }}
              >
                Level {caseData.triage?.urgency_level ?? "—"} · {severity.label}
              </span>

              <span>·</span>

              <span>waiting {formatWaitingTime(liveWaitingSeconds)}</span>
            </div>
          </div>
        </div>

        <WorkflowActions
          caseData={caseData}
          isActing={isActing}
          onCall={onCall}
          onComplete={onComplete}
          onStart={onStart}
          queueEntry={queueEntry}
        />
      </div>

      {caseData.triage?.red_flags_present && (
        <div className="motion-safe:animate-in motion-safe:fade-in-0 motion-safe:slide-in-from-top-1 mt-4 flex items-center gap-2.5 rounded-md border border-danger/35 bg-[color-mix(in_srgb,var(--aurora-danger)_12%,var(--aurora-surface))] px-3.5 py-2.75 text-[13px] font-bold text-danger motion-safe:duration-300">
          <AlertTriangle className="size-4.5 shrink-0" />
          Red flag signals present — reviewed by triage policy, not an AI
          diagnosis
        </div>
      )}

      <WorkflowStepper status={caseData.session.status} />
    </div>
  );
}
