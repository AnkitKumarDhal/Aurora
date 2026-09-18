import { ArrowLeft } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import DoctorHeader from "@/components/layout/DoctorHeader";
import { useAuth } from "@/auth/useAuth";
import CaseSkeleton from "@/features/case/components/CaseSkeleton";
import CaseHeader from "@/features/case/components/CaseHeader";
import ClinicalSummaryPanel from "@/features/case/components/ClinicalSummaryPanel";
import DocumentsPanel from "@/features/case/components/DocumentsPanel";
import IdentityPanel from "@/features/case/components/IdentityPanel";
import TriagePanel from "@/features/case/components/TriagePanel";
import { useCasePage } from "@/features/case/hooks/useCasePage";

export default function CasePage() {
  const { user, logout } = useAuth();
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  const {
    caseData,
    queueEntry,
    liveWaitingSeconds,
    isLoading,
    isActing,
    isSaving,
    isConfirming,
    isEditing,
    error,
    form,
    setForm,
    handleCall,
    handleStart,
    handleComplete,
    handleEdit,
    handleSaveSummary,
    handleConfirmSummary,
    cancelEditing,
  } = useCasePage(sessionId);

  return (
    <main className="min-h-screen bg-background">
      <DoctorHeader user={user} onLogout={logout} />

      <div className="mx-auto w-full max-w-295 px-7 pb-16 pt-7">
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
                  onCancel={cancelEditing}
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
