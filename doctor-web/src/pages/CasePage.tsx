import { useCallback, useEffect, useState } from "react";
import {
  AlertTriangle,
  ArrowLeft,
  Check,
  FileText,
  LoaderCircle,
  Phone,
  Play,
} from "lucide-react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import DoctorHeader from "@/components/layout/DoctorHeader";
import { useAuth } from "@/auth/useAuth";
import { getDoctorCase } from "@/api/case";
import { getDoctorQueueEntry } from "@/api/queue";
import {
  callPatient,
  completeConsultation,
  startConsultation,
} from "@/api/workflow";
import { confirmSummary, updateSummary } from "@/api/summary";
import type {
  ClinicalSummary,
  DoctorCaseResponse,
  DoctorQueueEntry,
  SessionStatus,
  UrgencyLevel,
} from "@/types/api";
import { useElapsedSeconds } from "@/hooks/useElapsedSeconds";

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);

  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }

  return name.slice(0, 2).toUpperCase();
}

function formatDate(value: string | null): string {
  if (!value) {
    return "—";
  }

  return value.slice(0, 10);
}

function formatWaitingTime(seconds: number | null): string {
  if (seconds === null) {
    return "—";
  }

  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;

  if (hours > 0) {
    return `${hours}h ${remainingMinutes}m`;
  }

  return `${remainingMinutes}m`;
}

function severityMeta(level: UrgencyLevel | null): {
  background: string;
  color: string;
  border: string;
  label: string;
} {
  switch (level) {
    case 1:
      return {
        background: "var(--aurora-primary-tint)",
        color: "var(--aurora-primary-dark)",
        border: "var(--aurora-success)",
        label: "Routine",
      };
    case 2:
      return {
        background: "var(--aurora-primary-tint)",
        color: "var(--aurora-primary-dark)",
        border: "var(--aurora-primary)",
        label: "Low",
      };
    case 3:
      return {
        background:
          "color-mix(in srgb, var(--aurora-warning) 18%, var(--aurora-surface))",
        color: "var(--aurora-text-primary)",
        border: "var(--aurora-warning)",
        label: "Moderate",
      };
    case 4:
      return {
        background: "var(--aurora-accent-tint)",
        color: "var(--aurora-accent-dark)",
        border: "var(--aurora-accent)",
        label: "Elevated",
      };
    case 5:
      return {
        background:
          "color-mix(in srgb, var(--aurora-danger) 14%, var(--aurora-surface))",
        color: "var(--aurora-danger)",
        border: "var(--aurora-danger)",
        label: "Critical",
      };
    default:
      return {
        background: "var(--aurora-primary-tint)",
        color: "var(--aurora-text-primary)",
        border: "var(--aurora-border)",
        label: "Unrated",
      };
  }
}

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

function statusLabel(status: string): string {
  return status
    .toLowerCase()
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
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
    <div className="mt-[18px] flex flex-wrap items-center">
      {steps.map((step, index) => {
        const done = index < currentIndex;
        const current = index === currentIndex;

        return (
          <div className="flex items-center" key={step.status}>
            <div className="flex items-center gap-2">
              <span
                className={[
                  "flex size-[22px] items-center justify-center rounded-full border-2 text-[10px] font-extrabold",
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
                  "text-xs font-bold",
                  done || current ? "text-primary-dark" : "text-text-secondary",
                ].join(" ")}
              >
                {step.label}
              </span>
            </div>

            {index < steps.length - 1 && (
              <span
                className={[
                  "mx-1.5 h-0.5 w-7",
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

  if (status === "ASSIGNED") {
    return (
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
    );
  }

  if (status === "CALLED") {
    return (
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
    );
  }

  if (status === "IN_CONSULTATION") {
    return (
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
    );
  }

  return (
    <span className="rounded-full bg-primary-tint px-3 py-2 text-[11px] font-bold text-text-secondary">
      Consultation completed
    </span>
  );
}

function TagList({
  items,
  muted = false,
}: {
  items: string[];
  muted?: boolean;
}) {
  if (items.length === 0) {
    return (
      <span className="text-xs italic text-text-secondary">None recorded</span>
    );
  }

  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((item) => (
        <span
          className={[
            "rounded-full px-2.5 py-1 text-xs font-semibold",
            muted
              ? "bg-primary-tint text-primary-dark"
              : "bg-accent-tint text-accent-dark",
          ].join(" ")}
          key={item}
        >
          {item}
        </span>
      ))}
    </div>
  );
}

function SummaryView({ summary }: { summary: ClinicalSummary }) {
  return (
    <div>
      <div className="mb-4">
        <div className="mb-1.5 text-[11.5px] font-bold text-text-secondary">
          Chief complaint
        </div>
        <div className="text-sm leading-[1.55]">
          {summary.chief_complaint ?? "—"}
        </div>
      </div>

      <div className="mb-4">
        <div className="mb-1.5 text-[11.5px] font-bold text-text-secondary">
          History of present illness
        </div>
        <div className="text-sm leading-[1.55]">
          {summary.history_of_present_illness ?? "—"}
        </div>
      </div>

      <div className="mb-4">
        <div className="mb-1.5 text-[11.5px] font-bold text-text-secondary">
          Past medical history
        </div>
        <TagList items={summary.past_medical_history} muted />
      </div>

      <div className="mb-4">
        <div className="mb-1.5 text-[11.5px] font-bold text-text-secondary">
          Medications
        </div>
        <TagList items={summary.medications} />
      </div>

      <div>
        <div className="mb-1.5 text-[11.5px] font-bold text-text-secondary">
          Allergies
        </div>
        <TagList items={summary.allergies} />
      </div>
    </div>
  );
}

function SummaryEdit({
  summary,
  form,
  setForm,
}: {
  summary: ClinicalSummary;
  form: {
    chief_complaint: string;
    history_of_present_illness: string;
    past_medical_history: string;
    medications: string;
    allergies: string;
  };
  setForm: React.Dispatch<
    React.SetStateAction<{
      chief_complaint: string;
      history_of_present_illness: string;
      past_medical_history: string;
      medications: string;
      allergies: string;
    }>
  >;
}) {
  return (
    <div>
      <div className="mb-4">
        <label
          className="mb-1.5 block text-[11.5px] font-bold text-text-secondary"
          htmlFor="edit-chief-complaint"
        >
          Chief complaint
        </label>
        <input
          className="w-full rounded-md border-[1.5px] border-border bg-surface-alt px-3 py-2 text-sm text-text-primary outline-none focus:border-primary focus:ring-2 focus:ring-primary-tint"
          id="edit-chief-complaint"
          onChange={(event) =>
            setForm((current) => ({
              ...current,
              chief_complaint: event.target.value,
            }))
          }
          value={form.chief_complaint}
        />
      </div>

      <div className="mb-4">
        <label
          className="mb-1.5 block text-[11.5px] font-bold text-text-secondary"
          htmlFor="edit-hpi"
        >
          History of present illness
        </label>
        <textarea
          className="min-h-24 w-full resize-y rounded-md border-[1.5px] border-border bg-surface-alt px-3 py-2 text-sm leading-[1.55] text-text-primary outline-none focus:border-primary focus:ring-2 focus:ring-primary-tint"
          id="edit-hpi"
          onChange={(event) =>
            setForm((current) => ({
              ...current,
              history_of_present_illness: event.target.value,
            }))
          }
          value={form.history_of_present_illness}
        />
      </div>

      <div className="mb-4">
        <label
          className="mb-1.5 block text-[11.5px] font-bold text-text-secondary"
          htmlFor="edit-pmh"
        >
          Past medical history
        </label>
        <input
          className="w-full rounded-md border-[1.5px] border-border bg-surface-alt px-3 py-2 text-sm text-text-primary outline-none focus:border-primary focus:ring-2 focus:ring-primary-tint"
          id="edit-pmh"
          onChange={(event) =>
            setForm((current) => ({
              ...current,
              past_medical_history: event.target.value,
            }))
          }
          placeholder="Separate items with commas"
          value={form.past_medical_history}
        />
      </div>

      <div className="mb-4">
        <label
          className="mb-1.5 block text-[11.5px] font-bold text-text-secondary"
          htmlFor="edit-medications"
        >
          Medications
        </label>
        <input
          className="w-full rounded-md border-[1.5px] border-border bg-surface-alt px-3 py-2 text-sm text-text-primary outline-none focus:border-primary focus:ring-2 focus:ring-primary-tint"
          id="edit-medications"
          onChange={(event) =>
            setForm((current) => ({
              ...current,
              medications: event.target.value,
            }))
          }
          placeholder="Separate items with commas"
          value={form.medications}
        />
      </div>

      <div>
        <label
          className="mb-1.5 block text-[11.5px] font-bold text-text-secondary"
          htmlFor="edit-allergies"
        >
          Allergies
        </label>
        <input
          className="w-full rounded-md border-[1.5px] border-border bg-surface-alt px-3 py-2 text-sm text-text-primary outline-none focus:border-primary focus:ring-2 focus:ring-primary-tint"
          id="edit-allergies"
          onChange={(event) =>
            setForm((current) => ({
              ...current,
              allergies: event.target.value,
            }))
          }
          placeholder="Separate items with commas"
          value={form.allergies}
        />
      </div>

      <span className="sr-only">{summary.summary_id}</span>
    </div>
  );
}

function ClinicalSummaryPanel({
  summary,
  isEditing,
  isSaving,
  isConfirming,
  form,
  setForm,
  onEdit,
  onSave,
  onCancel,
  onConfirm,
}: {
  summary: ClinicalSummary | null;
  isEditing: boolean;
  isSaving: boolean;
  isConfirming: boolean;
  form: {
    chief_complaint: string;
    history_of_present_illness: string;
    past_medical_history: string;
    medications: string;
    allergies: string;
  };
  setForm: React.Dispatch<
    React.SetStateAction<{
      chief_complaint: string;
      history_of_present_illness: string;
      past_medical_history: string;
      medications: string;
      allergies: string;
    }>
  >;
  onEdit: () => void;
  onSave: () => void;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  return (
    <Card className="rounded-[20px] border border-border bg-surface p-0 shadow-none">
      <CardHeader className="flex flex-row items-center justify-between gap-3 px-[22px] pb-0 pt-5">
        <CardTitle className="font-display text-[15.5px] font-semibold text-primary-dark">
          Clinical summary
        </CardTitle>

        {summary && (
          <span
            className="rounded-full px-[9px] py-[3px] text-[10.5px] font-extrabold"
            style={{
              background:
                summary.status === "CONFIRMED"
                  ? "color-mix(in srgb, var(--aurora-success) 20%, var(--aurora-surface))"
                  : "var(--aurora-primary-tint)",
              color:
                summary.status === "CONFIRMED"
                  ? "color-mix(in srgb, var(--aurora-success) 55%, var(--aurora-text-primary))"
                  : "var(--aurora-primary-dark)",
            }}
          >
            {summary.status === "CONFIRMED" ? "Confirmed" : "AI-generated"}
          </span>
        )}
      </CardHeader>

      <CardContent className="px-[22px] pb-5 pt-[14px]">
        {!summary ? (
          <span className="text-xs italic text-text-secondary">
            No clinical summary available.
          </span>
        ) : isEditing ? (
          <SummaryEdit form={form} setForm={setForm} summary={summary} />
        ) : (
          <SummaryView summary={summary} />
        )}

        {summary && (
          <div className="mt-[18px] flex gap-2 border-t border-border pt-4">
            {isEditing ? (
              <>
                <Button
                  className="h-9 rounded-md border border-primary bg-primary-tint px-4 text-xs font-bold text-primary-dark hover:bg-primary-tint"
                  disabled={isSaving}
                  onClick={onSave}
                  type="button"
                  variant="outline"
                >
                  {isSaving ? (
                    <>
                      <LoaderCircle className="size-4 animate-spin" />
                      Saving
                    </>
                  ) : (
                    "Save changes"
                  )}
                </Button>

                <Button
                  className="h-9 rounded-md px-4 text-xs font-bold text-text-secondary"
                  disabled={isSaving}
                  onClick={onCancel}
                  type="button"
                  variant="ghost"
                >
                  Cancel
                </Button>
              </>
            ) : (
              <>
                <Button
                  className="h-9 rounded-md border border-border bg-surface-alt px-4 text-xs font-bold text-text-secondary hover:bg-primary-tint hover:text-primary-dark"
                  onClick={onEdit}
                  type="button"
                  variant="outline"
                >
                  Edit summary
                </Button>

                <Button
                  className="h-9 flex-1 rounded-md bg-primary-dark text-xs font-bold text-surface hover:bg-primary-dark/90"
                  disabled={isConfirming || summary.status === "CONFIRMED"}
                  onClick={onConfirm}
                  type="button"
                >
                  {isConfirming ? (
                    <>
                      <LoaderCircle className="size-4 animate-spin" />
                      Confirming
                    </>
                  ) : summary.status === "CONFIRMED" ? (
                    <>
                      <Check className="size-4" />
                      Summary confirmed
                    </>
                  ) : (
                    "Confirm summary"
                  )}
                </Button>
              </>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function DocumentsPanel({
  documents,
}: {
  documents: DoctorCaseResponse["documents"];
}) {
  return (
    <Card className="rounded-[20px] border border-border bg-surface p-0 shadow-none mt-4">
      <CardHeader className="flex flex-row items-center justify-between px-[22px] pb-0 pt-5">
        <CardTitle className="font-display text-[15.5px] font-semibold text-primary-dark">
          Documents
        </CardTitle>
        <span className="text-[11.5px] text-text-secondary">
          {documents.length} {documents.length === 1 ? "file" : "files"}
        </span>
      </CardHeader>

      <CardContent className="px-[22px] pb-5 pt-[14px]">
        {documents.length === 0 ? (
          <span className="text-xs italic text-text-secondary">
            No documents uploaded for this session
          </span>
        ) : (
          <div className="flex flex-col gap-2">
            {documents.map((document) => {
              const processed = document.status === "PROCESSED";
              const failed = document.status === "FAILED";

              return (
                <div
                  className="flex items-center gap-2.5 rounded-md border border-border bg-surface-alt px-3 py-2.5"
                  key={document.document_id}
                >
                  <span className="flex size-[30px] shrink-0 items-center justify-center rounded-lg bg-primary-tint text-primary-dark">
                    <FileText className="size-[15px]" />
                  </span>

                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[13px] font-bold text-text-primary">
                      {document.filename}
                    </p>
                    <p className="text-[11px] text-text-secondary">
                      {document.document_type.replace(/_/g, " ").toLowerCase()}
                    </p>
                  </div>

                  <span
                    className="shrink-0 rounded-full px-[9px] py-[3px] text-[10.5px] font-extrabold"
                    style={{
                      background: processed
                        ? "color-mix(in srgb, var(--aurora-success) 18%, var(--aurora-surface))"
                        : failed
                          ? "color-mix(in srgb, var(--aurora-danger) 16%, var(--aurora-surface))"
                          : "var(--aurora-accent-tint)",
                      color: processed
                        ? "color-mix(in srgb, var(--aurora-success) 55%, var(--aurora-text-primary))"
                        : failed
                          ? "var(--aurora-danger)"
                          : "var(--aurora-accent-dark)",
                    }}
                  >
                    {document.status.toLowerCase()}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function TriagePanel({ triage }: { triage: DoctorCaseResponse["triage"] }) {
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

  const severity = severityMeta(triage.urgency_level);

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
            className="text-[13.5px] font-extrabold"
            style={{ color: severity.color }}
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
            {statusLabel(triage.status)}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

function IdentityPanel({
  patient,
}: {
  patient: DoctorCaseResponse["patient"];
}) {
  if (!patient) {
    return null;
  }

  const rows = [
    ["Patient ID", patient.patient_id],
    ["Date of birth", formatDate(patient.date_of_birth)],
    ["ABHA reference", patient.abha_reference ?? "Not linked"],
    ["Hospital reference", patient.hospital_reference ?? "—"],
  ];

  return (
    <Card className="rounded-[20px] border border-border bg-surface p-0 shadow-none mt-4">
      <CardHeader className="px-[22px] pb-0 pt-5">
        <CardTitle className="font-display text-[15.5px] font-semibold text-primary-dark">
          Patient identity
        </CardTitle>
      </CardHeader>

      <CardContent className="px-[22px] pb-5 pt-[14px]">
        {rows.map(([label, value], index) => (
          <div
            className={[
              "flex items-center justify-between gap-4 py-2 text-[13px]",
              index === rows.length - 1
                ? "border-b-0 pb-0"
                : "border-b border-border",
            ].join(" ")}
            key={label}
          >
            <span className="text-text-secondary">{label}</span>
            <span className="text-right font-bold text-text-primary">
              {value}
            </span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

export default function CasePage() {
  const { user, logout } = useAuth();
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [caseData, setCaseData] = useState<DoctorCaseResponse | null>(null);
  const [queueEntry, setQueueEntry] = useState<DoctorQueueEntry | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isActing, setIsActing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");
  const [form, setForm] = useState({
    chief_complaint: "",
    history_of_present_illness: "",
    past_medical_history: "",
    medications: "",
    allergies: "",
  });

  const liveWaitingSeconds = useElapsedSeconds(
    queueEntry?.waiting_time_seconds ?? null,
    queueEntry?.queued_at ?? null,
    queueEntry?.status === "WAITING" ||
      queueEntry?.status === "PROMOTION_PENDING",
  );

  const queueEntryIdFromUrl = searchParams.get("queueEntryId");

  const applyCase = useCallback(
    (response: DoctorCaseResponse, entry: DoctorQueueEntry | null): void => {
      setCaseData(response);
      setQueueEntry(entry);

      if (response.summary) {
        setForm({
          chief_complaint: response.summary.chief_complaint ?? "",
          history_of_present_illness:
            response.summary.history_of_present_illness ?? "",
          past_medical_history:
            response.summary.past_medical_history.join(", "),
          medications: response.summary.medications.join(", "),
          allergies: response.summary.allergies.join(", "),
        });
      }
    },
    [],
  );

  const loadCase = useCallback(async (): Promise<void> => {
    if (!sessionId) {
      return;
    }

    try {
      const [response, entry] = await Promise.all([
        getDoctorCase(sessionId),
        getDoctorQueueEntry(sessionId),
      ]);

      applyCase(response, entry);
      setError("");
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "Unable to load patient case",
      );
    } finally {
      setIsLoading(false);
    }
  }, [applyCase, sessionId]);

  useEffect(() => {
    if (!sessionId) {
      return;
    }

    let cancelled = false;

    Promise.all([getDoctorCase(sessionId), getDoctorQueueEntry(sessionId)])
      .then(([response, entry]) => {
        if (cancelled) {
          return;
        }

        applyCase(response, entry);
        setError("");
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }

        setError(
          error instanceof Error
            ? error.message
            : "Unable to load patient case",
        );
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [applyCase, sessionId]);

  useEffect(() => {
    if (!queueEntryIdFromUrl) {
      return;
    }

    const interval = window.setInterval(() => {
      void loadCase();
    }, 15000);

    return () => {
      window.clearInterval(interval);
    };
  }, [loadCase, queueEntryIdFromUrl]);

  function showToast(message: string): void {
    setToast(message);
    window.setTimeout(() => {
      setToast("");
    }, 2600);
  }

  async function handleCall(): Promise<void> {
    if (!sessionId || !queueEntry) {
      return;
    }

    setIsActing(true);
    setError("");

    try {
      await callPatient(sessionId, queueEntry.queue_entry_id);
      await loadCase();
      showToast(`Patient called`);
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "Unable to call patient",
      );
    } finally {
      setIsActing(false);
    }
  }

  async function handleStart(): Promise<void> {
    if (!sessionId || !queueEntry) {
      return;
    }

    setIsActing(true);
    setError("");

    try {
      await startConsultation(sessionId, queueEntry.queue_entry_id);
      await loadCase();
      showToast(`Consultation Started`);
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "Unable to start consultation",
      );
    } finally {
      setIsActing(false);
    }
  }

  async function handleComplete(): Promise<void> {
    if (
      !sessionId ||
      !queueEntry ||
      caseData?.summary?.status !== "CONFIRMED"
    ) {
      return;
    }

    setIsActing(true);
    setError("");

    try {
      await completeConsultation(sessionId, queueEntry.queue_entry_id);
      await loadCase();
      showToast(`Complete Consultation`);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Unable to complete consultation",
      );
    } finally {
      setIsActing(false);
    }
  }

  function handleEdit(): void {
    if (!caseData?.summary) {
      return;
    }

    setForm({
      chief_complaint: caseData.summary.chief_complaint ?? "",
      history_of_present_illness:
        caseData.summary.history_of_present_illness ?? "",
      past_medical_history: caseData.summary.past_medical_history.join(", "),
      medications: caseData.summary.medications.join(", "),
      allergies: caseData.summary.allergies.join(", "),
    });

    setIsEditing(true);
  }

  function parseList(value: string): string[] {
    return value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  }

  async function handleSaveSummary(): Promise<void> {
    if (!sessionId) {
      return;
    }

    setIsSaving(true);
    setError("");

    try {
      await updateSummary(sessionId, {
        chief_complaint: form.chief_complaint.trim() || null,
        history_of_present_illness:
          form.history_of_present_illness.trim() || null,
        past_medical_history: parseList(form.past_medical_history),
        medications: parseList(form.medications),
        allergies: parseList(form.allergies),
      });

      setIsEditing(false);
      await loadCase();
      showToast(`Summary Saved`);
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "Unable to save summary",
      );
    } finally {
      setIsSaving(false);
    }
  }

  async function handleConfirmSummary(): Promise<void> {
    if (!sessionId) {
      return;
    }

    setIsConfirming(true);
    setError("");

    try {
      await confirmSummary(sessionId);
      await loadCase();
      showToast(`Summary Confirmed`);
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "Unable to confirm summary",
      );
    } finally {
      setIsConfirming(false);
    }
  }

  const severity = severityMeta(caseData?.triage?.urgency_level ?? null);

  return (
    <main className="min-h-screen bg-background">
      <DoctorHeader user={user} onLogout={logout} />

      <div className="mx-auto w-full max-w-[1180px] px-7 pb-16 pt-7">
        <Button
          className="mb-4 h-auto gap-1.5 px-0 py-1.5 text-[13px] font-bold text-text-secondary hover:bg-transparent hover:text-primary-dark"
          onClick={() => navigate("/queue")}
          type="button"
          variant="ghost"
        >
          <ArrowLeft className="size-3.5" />
          Back to queue
        </Button>

        {isLoading ? (
          <div className="rounded-[20px] border border-border bg-surface px-5 py-16 text-center">
            <p className="text-[13px] text-text-secondary">
              Loading patient case...
            </p>
          </div>
        ) : error && !caseData ? (
          <div className="rounded-[20px] border border-border bg-surface px-5 py-10">
            <p className="text-[13px] text-danger">{error}</p>
            <Button
              className="mt-4"
              onClick={() => navigate("/queue")}
              type="button"
              variant="outline"
            >
              Back to queue
            </Button>
          </div>
        ) : caseData ? (
          <>
            <Card className="rounded-[20px] border border-border bg-surface p-0 shadow-none">
              <CardContent className="px-6 py-[22px]">
                <div className="flex flex-wrap items-start justify-between gap-5">
                  <div className="flex items-center gap-3.5">
                    <span className="flex size-[52px] shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-primary-tint to-accent-tint font-display text-lg font-semibold text-primary-dark">
                      {initials(caseData.patient?.display_name ?? "Patient")}
                    </span>

                    <div>
                      <h1 className="font-display text-[21px] font-semibold text-primary-dark">
                        {caseData.patient?.display_name ?? "Unknown patient"}
                      </h1>

                      <div className="mt-[3px] flex flex-wrap items-center gap-2.5 text-[12.5px] text-text-secondary">
                        <span>
                          {caseData.patient?.age !== null &&
                          caseData.patient?.age !== undefined
                            ? `${caseData.patient.age} yrs`
                            : "Age unknown"}
                        </span>

                        <span>·</span>

                        <span
                          className="rounded-full px-[9px] py-[3px] text-[10.5px] font-extrabold"
                          style={{
                            background: severity.background,
                            color: severity.color,
                          }}
                        >
                          Level {caseData.triage?.urgency_level ?? "—"} ·{" "}
                          {severity.label}
                        </span>

                        <span>·</span>

                        <span>
                          waiting {formatWaitingTime(liveWaitingSeconds)}
                        </span>
                      </div>
                    </div>
                  </div>

                  <WorkflowActions
                    caseData={caseData}
                    isActing={isActing}
                    onCall={handleCall}
                    onComplete={handleComplete}
                    onStart={handleStart}
                    queueEntry={queueEntry}
                  />
                </div>

                {caseData.triage?.red_flags_present && (
                  <div className="mt-4 flex items-center gap-2.5 rounded-md border border-danger/35 bg-[color-mix(in_srgb,var(--aurora-danger)_12%,var(--aurora-surface))] px-3.5 py-[11px] text-[13px] font-bold text-danger">
                    <AlertTriangle className="size-[18px] shrink-0" />
                    Red flag signals present — reviewed by triage policy, not an
                    AI diagnosis
                  </div>
                )}

                <WorkflowStepper status={caseData.session.status} />
              </CardContent>
            </Card>

            {error && (
              <div className="mt-5 rounded-lg border border-danger/30 bg-accent-tint px-4 py-3">
                <p className="text-[13px] text-danger">{error}</p>
              </div>
            )}

            <div className="mt-5 grid items-start gap-5 lg:grid-cols-[1.6fr_1fr]">
              <div>
                <ClinicalSummaryPanel
                  form={form}
                  isConfirming={isConfirming}
                  isEditing={isEditing}
                  isSaving={isSaving}
                  onCancel={() => setIsEditing(false)}
                  onConfirm={handleConfirmSummary}
                  onEdit={handleEdit}
                  onSave={handleSaveSummary}
                  setForm={setForm}
                  summary={caseData.summary}
                />

                <DocumentsPanel documents={caseData.documents} />
              </div>

              <div>
                <TriagePanel triage={caseData.triage} />
                <IdentityPanel patient={caseData.patient} />
              </div>
            </div>
          </>
        ) : null}
      </div>

      {toast && (
        <div className="fixed bottom-[26px] left-1/2 z-50 flex -translate-x-1/2 items-center gap-2 rounded-full bg-primary-dark px-5 py-3 text-[13px] font-bold text-surface shadow-[0_18px_40px_-14px_rgba(58,46,92,0.6)]">
          <span className="size-[7px] shrink-0 rounded-full bg-accent" />
          {toast}
        </div>
      )}
    </main>
  );
}
