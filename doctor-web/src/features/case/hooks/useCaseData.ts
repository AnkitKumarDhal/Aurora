import { useCallback, useEffect, useState } from "react";
import { getApiErrorMessage } from "@/api/client";
import { getDoctorCase } from "@/api/case";
import { getDoctorQueueEntry } from "@/api/queue";
import type { DoctorCaseResponse, DoctorQueueEntry } from "@/types/api";

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

  const applyCase = useCallback(
    (response: DoctorCaseResponse, entry: DoctorQueueEntry | null): void => {
      setCaseData(response);
      setQueueEntry(entry);
    },
    [],
  );

  const refresh = useCallback(async (): Promise<void> => {
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

    const initialLoad = window.setTimeout(() => {
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

          setError(getApiErrorMessage(error, "Unable to load patient case."));
        })
        .finally(() => {
          if (!cancelled) {
            setIsLoading(false);
          }
        });
    }, 0);

    const interval = window.setInterval(() => {
      if (cancelled) {
        return;
      }

      void refresh().catch(() => {});
    }, 15000);

    return () => {
      cancelled = true;
      window.clearTimeout(initialLoad);
      window.clearInterval(interval);
    };
  }, [applyCase, refresh, sessionId]);

  return {
    caseData,
    queueEntry,
    isLoading,
    error,
    refresh,
  };
}
