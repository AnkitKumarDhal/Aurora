import { useCallback, useEffect, useState } from "react";
import { getApiErrorMessage } from "@/api/client";
import { getDoctorQueue } from "@/api/queue";
import type { DoctorQueueEntry } from "@/types/api";

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
    const initialLoad = window.setTimeout(() => {
      void refresh();
    }, 0);

    const interval = window.setInterval(() => {
      void refresh();
    }, 15000);

    return () => {
      window.clearTimeout(initialLoad);
      window.clearInterval(interval);
    };
  }, [refresh]);

  return {
    entries,
    isLoading,
    error,
    refresh,
  };
}
