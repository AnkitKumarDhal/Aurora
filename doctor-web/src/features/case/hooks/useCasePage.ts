import { useElapsedSeconds } from "@/hooks/useElapsedSeconds";
import { useCaseActions } from "./useCaseActions";
import { useCaseData } from "./useCaseData";
import { useSummaryEditor } from "./useSummaryEditor";

export function useCasePage(sessionId: string | undefined) {
  const { caseData, queueEntry, isLoading, error, refresh } =
    useCaseData(sessionId);

  const {
    form,
    setForm,
    isEditing,
    isSaving,
    isConfirming,
    beginEditing,
    cancelEditing,
    saveSummary,
    confirm,
  } = useSummaryEditor(sessionId, caseData?.summary ?? null, refresh);

  const { isActing, call, start, complete } = useCaseActions(
    sessionId,
    caseData,
    queueEntry,
    refresh,
  );

  const liveWaitingSeconds = useElapsedSeconds(
    queueEntry?.waiting_time_seconds ?? null,
    queueEntry?.queued_at ?? null,
    queueEntry?.status === "WAITING" ||
      queueEntry?.status === "PROMOTION_PENDING",
  );

  return {
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
    handleCall: call,
    handleStart: start,
    handleComplete: complete,
    handleEdit: beginEditing,
    handleSaveSummary: saveSummary,
    handleConfirmSummary: confirm,
    cancelEditing,
  };
}
