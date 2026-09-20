import { useCallback, useEffect, useRef, useState } from "react";

import { getApiErrorMessage } from "@/api/client";
import { getDoctorCase } from "@/api/case";
import { getDoctorQueueEntry } from "@/api/queue";
import { subscribeToEvents } from "@/api/events";

import type { DoctorCaseResponse, DoctorQueueEntry } from "@/types/api";

const DEPARTMENT_ID = "general-medicine";

interface UseCaseDataResult {
  caseData: DoctorCaseResponse | null;
  queueEntry: DoctorQueueEntry | null;
  isLoading: boolean;
  error: string;
  refresh: () => Promise<void>;
}

export function useCaseData(sessionId: string | undefined): UseCaseDataResult {
  const [caseData, setCaseData] = useState<DoctorCaseResponse | null>(null);
  const [queueEntry, setQueueEntry] = useState<DoctorQueueEntry | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const refreshTimerRef = useRef<number | null>(null);

  const refresh = useCallback(async (): Promise<void> => {
    if (!sessionId) {
      return;
    }

    try {
      const [response, entry] = await Promise.all([
        getDoctorCase(sessionId),
        getDoctorQueueEntry(sessionId),
      ]);

      setCaseData(response);
      setQueueEntry(entry);
      setError("");
    } catch (error) {
      setError(getApiErrorMessage(error, "Unable to load patient case."));
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    if (!sessionId) {
      return;
    }

    const scheduleRefresh = (): void => {
      if (refreshTimerRef.current !== null) {
        window.clearTimeout(refreshTimerRef.current);
      }

      refreshTimerRef.current = window.setTimeout(() => {
        refreshTimerRef.current = null;
        void refresh();
      }, 100);
    };

    const initialLoad = window.setTimeout(() => {
      void refresh();
    }, 0);

    const unsubscribe = subscribeToEvents(DEPARTMENT_ID, () => {
      scheduleRefresh();
    });

    return () => {
      window.clearTimeout(initialLoad);
      unsubscribe();

      if (refreshTimerRef.current !== null) {
        window.clearTimeout(refreshTimerRef.current);
        refreshTimerRef.current = null;
      }
    };
  }, [refresh, sessionId]);

  return {
    caseData,
    queueEntry,
    isLoading,
    error,
    refresh,
  };
}
