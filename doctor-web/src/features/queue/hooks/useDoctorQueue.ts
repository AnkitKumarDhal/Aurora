import { useCallback, useEffect, useRef, useState } from "react";

import { getApiErrorMessage } from "@/api/client";
import { subscribeToEvents } from "@/api/events";
import { getDoctorQueue } from "@/api/queue";

import type { DoctorQueueEntry } from "@/types/api";

const DEPARTMENT_ID = "general-medicine";

interface UseDoctorQueueResult {
  entries: DoctorQueueEntry[];
  isLoading: boolean;
  error: string;
  refresh: () => Promise<void>;
}

export function useDoctorQueue(): UseDoctorQueueResult {
  const [entries, setEntries] = useState<DoctorQueueEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const refreshTimerRef = useRef<number | null>(null);

  const refresh = useCallback(async (): Promise<void> => {
    try {
      const response = await getDoctorQueue();

      setEntries(response.entries);
      setError("");
    } catch (error) {
      setError(getApiErrorMessage(error, "Unable to load the queue."));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
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
  }, [refresh]);

  return {
    entries,
    isLoading,
    error,
    refresh,
  };
}
