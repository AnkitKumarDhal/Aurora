import { useCallback, useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
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
} from "@/types/api";
import { useElapsedSeconds } from "@/hooks/useElapsedSeconds";
import { toast } from "sonner";
import { getApiErrorMessage } from "@/api/client";
import CaseSkeleton from "@/components/CaseSkeleton";
import CaseHeader from "@/features/case/components/CaseHeader";
import ClinicalSummaryPanel from "@/features/case/components/ClinicalSummaryPanel";
import DocumentsPanel from "@/features/case/components/DocumentsPanel";
import IdentityPanel from "@/features/case/components/IdentityPanel";
import TriagePanel from "@/features/case/components/TriagePanel";

interface SummaryForm {
  chief_complaint: string;
  history_of_present_illness: string;
  past_medical_history: string;
  medications: string;
  allergies: string;
}

const EMPTY_FORM: SummaryForm = {
  chief_complaint: "",
  history_of_present_illness: "",
  past_medical_history: "",
  medications: "",
  allergies: "",
};

function summaryToForm(summary: ClinicalSummary): SummaryForm {
  return {
    chief_complaint: summary.chief_complaint ?? "",
    history_of_present_illness: summary.history_of_present_illness ?? "",
    past_medical_history: summary.past_medical_history.join(", "),
    medications: summary.medications.join(", "),
    allergies: summary.allergies.join(", "),
  };
}

function parseList(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
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
  const [form, setForm] = useState<SummaryForm>(EMPTY_FORM);

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
        setForm(summaryToForm(response.summary));
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

        setError(getApiErrorMessage(error, "Unable to load patient case"));
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
      void loadCase().catch(() => {});
    }, 15000);

    return () => {
      window.clearInterval(interval);
    };
  }, [loadCase, queueEntryIdFromUrl]);

  async function handleCall(): Promise<void> {
    if (!sessionId || !queueEntry) {
      return;
    }

    setIsActing(true);
    setError("");

    try {
      await callPatient(sessionId, queueEntry.queue_entry_id);
      await loadCase();
      toast.success("Patient called");
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Unable to call patient."));
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
      toast.success("Consultation started");
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Unable to start consultation."));
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
      toast.success("Consultation completed");
    } catch (error) {
      toast.error(
        getApiErrorMessage(error, "Unable to complete consultation."),
      );
    } finally {
      setIsActing(false);
    }
  }

  function handleEdit(): void {
    if (!caseData?.summary) {
      return;
    }

    setForm(summaryToForm(caseData.summary));
    setIsEditing(true);
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
      toast.success("Summary saved");
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Unable to save summary."));
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
      toast.success("Summary confirmed");
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Unable to confirm summary."));
    } finally {
      setIsConfirming(false);
    }
  }

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
          <CaseSkeleton />
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
            <CaseHeader
              caseData={caseData}
              isActing={isActing}
              liveWaitingSeconds={liveWaitingSeconds}
              onCall={handleCall}
              onComplete={handleComplete}
              onStart={handleStart}
              queueEntry={queueEntry}
            />

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

        {error && caseData && (
          <div className="mt-5 rounded-lg border border-danger/30 bg-accent-tint px-4 py-3">
            <p className="text-[13px] text-danger">{error}</p>
          </div>
        )}
      </div>
    </main>
  );
}
