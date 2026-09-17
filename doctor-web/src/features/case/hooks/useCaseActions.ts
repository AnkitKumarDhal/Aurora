import { useCallback, useState } from "react";
import { toast } from "sonner";
import { getApiErrorMessage } from "@/api/client";
import {
  callPatient,
  completeConsultation,
  startConsultation,
} from "@/api/workflow";
import type { DoctorCaseResponse, DoctorQueueEntry } from "@/types/api";

interface UseCaseActionsResult {
  isActing: boolean;
  call: () => Promise<void>;
  start: () => Promise<void>;
  complete: () => Promise<void>;
}

export function useCaseActions(
  sessionId: string | undefined,
  caseData: DoctorCaseResponse | null,
  queueEntry: DoctorQueueEntry | null,
  refresh: () => Promise<void>,
): UseCaseActionsResult {
  const [isActing, setIsActing] = useState(false);

  const call = useCallback(async (): Promise<void> => {
    if (!sessionId || !queueEntry) {
      return;
    }

    setIsActing(true);

    try {
      await callPatient(sessionId, queueEntry.queue_entry_id);
      await refresh();
      toast.success("Patient called");
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Unable to call patient."));
    } finally {
      setIsActing(false);
    }
  }, [queueEntry, refresh, sessionId]);

  const start = useCallback(async (): Promise<void> => {
    if (!sessionId || !queueEntry) {
      return;
    }

    setIsActing(true);

    try {
      await startConsultation(sessionId, queueEntry.queue_entry_id);
      await refresh();
      toast.success("Consultation started");
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Unable to start consultation."));
    } finally {
      setIsActing(false);
    }
  }, [queueEntry, refresh, sessionId]);

  const complete = useCallback(async (): Promise<void> => {
    if (
      !sessionId ||
      !queueEntry ||
      caseData?.summary?.status !== "CONFIRMED"
    ) {
      return;
    }

    setIsActing(true);

    try {
      await completeConsultation(sessionId, queueEntry.queue_entry_id);
      await refresh();
      toast.success("Consultation completed");
    } catch (error) {
      toast.error(
        getApiErrorMessage(error, "Unable to complete consultation."),
      );
    } finally {
      setIsActing(false);
    }
  }, [caseData, queueEntry, refresh, sessionId]);

  return {
    isActing,
    call,
    start,
    complete,
  };
}
