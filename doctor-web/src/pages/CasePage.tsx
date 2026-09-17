import { useCallback, useEffect, useState } from "react";
import {
  ArrowLeft,
  Check,
  Circle,
  FileText,
  LoaderCircle,
  Phone,
  Play,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { getDoctorCase } from "@/api/case";
import {
  callPatient,
  completeConsultation,
  startConsultation,
} from "@/api/workflow";
import { confirmSummary } from "@/api/summary";
import type {
  DoctorCaseResponse,
  SessionStatus,
  UrgencyLevel,
} from "@/types/api";

function formatDate(value: string | null): string {
  if (!value) {
    return "Not available";
  }

  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
  }).format(new Date(value));
}

function urgencyLabel(level: UrgencyLevel | null): string {
  return level === null ? "Unrated" : `Level ${level}`;
}

function urgencyVariant(
  level: UrgencyLevel | null,
): "default" | "secondary" | "outline" | "destructive" {
  switch (level) {
    case 4:
    case 5:
      return "destructive";
    case 3:
      return "default";
    case 1:
    case 2:
      return "secondary";
    default:
      return "outline";
  }
}

function statusLabel(status: string): string {
  return status
    .toLowerCase()
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function ListSection({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <h3 className="text-sm font-medium text-muted-foreground">{title}</h3>

      {items.length === 0 ? (
        <p className="mt-2 text-sm text-muted-foreground">Nothing recorded.</p>
      ) : (
        <ul className="mt-2 space-y-2">
          {items.map((item) => (
            <li
              className="rounded-lg border bg-background px-3 py-2 text-sm"
              key={item}
            >
              {item}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function PatientIdentity({
  patient,
}: {
  patient: NonNullable<DoctorCaseResponse["patient"]>;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <UserRound className="size-5" />
          Patient identity
        </CardTitle>
      </CardHeader>

      <CardContent className="grid gap-5 sm:grid-cols-2">
        <div>
          <p className="text-sm text-muted-foreground">Name</p>
          <p className="mt-1 font-medium">{patient.display_name}</p>
        </div>

        <div>
          <p className="text-sm text-muted-foreground">Age</p>
          <p className="mt-1 font-medium">
            {patient.age !== null ? `${patient.age} years` : "Not available"}
          </p>
        </div>

        <div>
          <p className="text-sm text-muted-foreground">Date of birth</p>
          <p className="mt-1 font-medium">
            {formatDate(patient.date_of_birth)}
          </p>
        </div>

        <div>
          <p className="text-sm text-muted-foreground">ABHA reference</p>
          <p className="mt-1 font-medium">
            {patient.abha_reference ?? "Not available"}
          </p>
        </div>

        <div>
          <p className="text-sm text-muted-foreground">Hospital reference</p>
          <p className="mt-1 font-medium">
            {patient.hospital_reference ?? "Not available"}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

function ClinicalSummary({
  caseData,
  isConfirming,
  onConfirm,
}: {
  caseData: DoctorCaseResponse;
  isConfirming: boolean;
  onConfirm: () => void;
}) {
  const summary = caseData.summary;

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <CardTitle>Clinical summary</CardTitle>

          {summary && (
            <div className="flex items-center gap-2">
              <Badge
                variant={
                  summary.status === "CONFIRMED" ? "default" : "secondary"
                }
              >
                {statusLabel(summary.status)}
              </Badge>

              {summary.status !== "CONFIRMED" && (
                <Button
                  disabled={isConfirming}
                  onClick={onConfirm}
                  size="sm"
                  type="button"
                >
                  {isConfirming ? (
                    <>
                      <LoaderCircle className="animate-spin" />
                      Confirming
                    </>
                  ) : (
                    <>
                      <Check />
                      Confirm summary
                    </>
                  )}
                </Button>
              )}
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {!summary ? (
          <p className="text-sm text-muted-foreground">
            No clinical summary is available yet.
          </p>
        ) : (
          <>
            <div>
              <h3 className="text-sm font-medium text-muted-foreground">
                Chief complaint
              </h3>
              <p className="mt-2 text-sm leading-6">
                {summary.chief_complaint ?? "Not recorded"}
              </p>
            </div>

            <Separator />

            <div>
              <h3 className="text-sm font-medium text-muted-foreground">
                History of present illness
              </h3>
              <p className="mt-2 text-sm leading-6">
                {summary.history_of_present_illness ?? "Not recorded"}
              </p>
            </div>

            <Separator />

            <ListSection
              title="Past medical history"
              items={summary.past_medical_history}
            />

            <Separator />

            <ListSection title="Medications" items={summary.medications} />

            <Separator />

            <ListSection title="Allergies" items={summary.allergies} />
          </>
        )}
      </CardContent>
    </Card>
  );
}

function DocumentsSection({
  documents,
}: {
  documents: DoctorCaseResponse["documents"];
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="size-5" />
          Documents
        </CardTitle>
      </CardHeader>

      <CardContent>
        {documents.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No documents attached to this case.
          </p>
        ) : (
          <div className="space-y-3">
            {documents.map((document) => (
              <div
                className="flex flex-col gap-3 rounded-xl border bg-background p-4 sm:flex-row sm:items-center sm:justify-between"
                key={document.document_id}
              >
                <div>
                  <p className="font-medium">{document.filename}</p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {document.document_type}
                  </p>
                </div>

                <Badge variant="outline">{statusLabel(document.status)}</Badge>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function TriageSection({ triage }: { triage: DoctorCaseResponse["triage"] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ShieldCheck className="size-5" />
          Triage
        </CardTitle>
      </CardHeader>

      <CardContent>
        {!triage ? (
          <p className="text-sm text-muted-foreground">
            No triage result is available.
          </p>
        ) : (
          <div className="space-y-5">
            <div className="flex flex-wrap gap-2">
              <Badge variant={urgencyVariant(triage.urgency_level)}>
                {urgencyLabel(triage.urgency_level)}
              </Badge>

              <Badge variant="outline">{statusLabel(triage.status)}</Badge>

              {triage.red_flags_present && (
                <Badge variant="destructive">Red flags present</Badge>
              )}
            </div>

            <div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Priority score</span>
                <span className="font-medium">
                  {triage.priority_score ?? "Not available"}
                </span>
              </div>

              {triage.priority_score !== null && (
                <div className="mt-3 h-2 overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-primary transition-all"
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

            <div>
              <p className="text-sm text-muted-foreground">Assessed</p>
              <p className="mt-1 text-sm">{formatDate(triage.assessed_at)}</p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

const WORKFLOW_STEPS: {
  status: SessionStatus;
  label: string;
}[] = [
  {
    status: "ASSIGNED",
    label: "Assigned",
  },
  {
    status: "CALLED",
    label: "Called",
  },
  {
    status: "IN_CONSULTATION",
    label: "In consultation",
  },
  {
    status: "COMPLETED",
    label: "Completed",
  },
];

function workflowStepIndex(status: SessionStatus): number {
  if (status === "COMPLETED") {
    return WORKFLOW_STEPS.length - 1;
  }

  const index = WORKFLOW_STEPS.findIndex((step) => step.status === status);

  return index === -1 ? 0 : index;
}

function WorkflowStepper({ status }: { status: SessionStatus }) {
  const activeIndex = workflowStepIndex(status);

  return (
    <div className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
      {WORKFLOW_STEPS.map((step, index) => {
        const complete = index < activeIndex;
        const active = index === activeIndex;

        return (
          <div className="flex items-center gap-3" key={step.status}>
            <div
              className={[
                "flex size-9 shrink-0 items-center justify-center rounded-full border",
                complete || active
                  ? "border-primary bg-primary text-primary-foreground"
                  : "border-border bg-card text-muted-foreground",
              ].join(" ")}
            >
              {complete ? (
                <Check className="size-4" />
              ) : active ? (
                <Circle className="size-3 fill-current" />
              ) : (
                <span className="size-2 rounded-full bg-current" />
              )}
            </div>

            <div>
              <p
                className={
                  active
                    ? "text-sm font-medium"
                    : "text-sm text-muted-foreground"
                }
              >
                {step.label}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function WorkflowActions({
  caseData,
  isActing,
  onCall,
  onStart,
  onComplete,
}: {
  caseData: DoctorCaseResponse;
  isActing: boolean;
  onCall: () => void;
  onStart: () => void;
  onComplete: () => void;
}) {
  const status = caseData.session.status;
  const summaryConfirmed = caseData.summary?.status === "CONFIRMED";

  if (status === "ASSIGNED") {
    return (
      <Button disabled={isActing} onClick={onCall} type="button">
        {isActing ? (
          <>
            <LoaderCircle className="animate-spin" />
            Calling
          </>
        ) : (
          <>
            <Phone />
            Call patient
          </>
        )}
      </Button>
    );
  }

  if (status === "CALLED") {
    return (
      <Button disabled={isActing} onClick={onStart} type="button">
        {isActing ? (
          <>
            <LoaderCircle className="animate-spin" />
            Starting
          </>
        ) : (
          <>
            <Play />
            Start consultation
          </>
        )}
      </Button>
    );
  }

  if (status === "IN_CONSULTATION") {
    return (
      <div className="flex flex-col items-stretch gap-3 sm:items-end">
        <Button
          disabled={isActing || !summaryConfirmed}
          onClick={onComplete}
          type="button"
        >
          {isActing ? (
            <>
              <LoaderCircle className="animate-spin" />
              Completing
            </>
          ) : (
            <>
              <Check />
              Complete consultation
            </>
          )}
        </Button>

        {!summaryConfirmed && (
          <p className="text-xs text-muted-foreground">
            Confirm the clinical summary before completing the consultation.
          </p>
        )}
      </div>
    );
  }

  return (
    <Badge className="h-9 px-4" variant="secondary">
      Consultation completed
    </Badge>
  );
}

export default function CasePage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  const [caseData, setCaseData] = useState<DoctorCaseResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isActing, setIsActing] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);
  const [error, setError] = useState("");

  const loadCase = useCallback(async (): Promise<void> => {
    if (!sessionId) {
      return;
    }

    try {
      const response = await getDoctorCase(sessionId);
      setCaseData(response);
      setError("");
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "Unable to load patient case",
      );
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    if (!sessionId) {
      return;
    }

    let cancelled = false;

    getDoctorCase(sessionId)
      .then((response) => {
        if (cancelled) {
          return;
        }

        setCaseData(response);
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
  }, [sessionId]);

  async function handleCall() {
    if (!caseData || !sessionId || !caseData.assignment) {
      return;
    }

    setIsActing(true);
    setError("");

    try {
      await callPatient(
        sessionId,
        caseData.assignment.session_id === sessionId
          ? getQueueEntryId(caseData)
          : getQueueEntryId(caseData),
      );
      await loadCase();
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "Unable to call patient",
      );
    } finally {
      setIsActing(false);
    }
  }

  async function handleStart() {
    if (!caseData || !sessionId) {
      return;
    }

    setIsActing(true);
    setError("");

    try {
      await startConsultation(sessionId, getQueueEntryId(caseData));
      await loadCase();
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "Unable to start consultation",
      );
    } finally {
      setIsActing(false);
    }
  }

  async function handleComplete() {
    if (!caseData || !sessionId || caseData.summary?.status !== "CONFIRMED") {
      return;
    }

    setIsActing(true);
    setError("");

    try {
      await completeConsultation(sessionId, getQueueEntryId(caseData));
      await loadCase();
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

  async function handleConfirmSummary() {
    if (!sessionId) {
      return;
    }

    setIsConfirming(true);
    setError("");

    try {
      await confirmSummary(sessionId);
      await loadCase();
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Unable to confirm clinical summary",
      );
    } finally {
      setIsConfirming(false);
    }
  }

  return (
    <main className="min-h-screen bg-background">
      <header className="border-b bg-background/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center gap-4 px-6 py-4">
          <Button
            onClick={() => navigate("/queue")}
            size="icon"
            variant="outline"
            type="button"
          >
            <ArrowLeft className="size-4" />
          </Button>

          <div>
            <p className="text-sm text-muted-foreground">Patient case</p>
            <h1 className="text-2xl font-semibold tracking-tight">
              {caseData?.patient?.display_name ?? "Loading case"}
            </h1>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-6 py-8">
        {isLoading ? (
          <div className="rounded-2xl border bg-card p-8 text-center">
            <p className="text-sm text-muted-foreground">
              Loading patient case...
            </p>
          </div>
        ) : error && !caseData ? (
          <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-6">
            <p className="text-sm text-destructive">{error}</p>

            <Button
              className="mt-4"
              onClick={() => navigate("/queue")}
              variant="outline"
              type="button"
            >
              Back to queue
            </Button>
          </div>
        ) : caseData ? (
          <>
            {error && (
              <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-4">
                <p className="text-sm text-destructive">{error}</p>
              </div>
            )}

            <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Session status</p>

                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <Badge>{statusLabel(caseData.session.status)}</Badge>

                  {caseData.triage && (
                    <Badge
                      variant={urgencyVariant(caseData.triage.urgency_level)}
                    >
                      {urgencyLabel(caseData.triage.urgency_level)}
                    </Badge>
                  )}
                </div>
              </div>

              <WorkflowActions
                caseData={caseData}
                isActing={isActing}
                onCall={handleCall}
                onComplete={handleComplete}
                onStart={handleStart}
              />
            </div>

            <WorkflowStepper status={caseData.session.status} />

            {caseData.triage?.red_flags_present && (
              <div className="mt-6 rounded-2xl border border-destructive/30 bg-destructive/5 p-5">
                <p className="font-medium text-destructive">
                  Red flags present
                </p>

                <p className="mt-1 text-sm text-muted-foreground">
                  Review the triage result and clinical information before
                  continuing.
                </p>
              </div>
            )}

            <div className="mt-8 grid gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]">
              <div className="space-y-6">
                <ClinicalSummary
                  caseData={caseData}
                  isConfirming={isConfirming}
                  onConfirm={handleConfirmSummary}
                />

                <DocumentsSection documents={caseData.documents} />
              </div>

              <div className="space-y-6">
                {caseData.patient && (
                  <PatientIdentity patient={caseData.patient} />
                )}

                <TriageSection triage={caseData.triage} />
              </div>
            </div>
          </>
        ) : null}
      </div>
    </main>
  );
}

function getQueueEntryId(caseData: DoctorCaseResponse): string {
  return caseData.assignment?.session_id ?? caseData.session.session_id;
}
