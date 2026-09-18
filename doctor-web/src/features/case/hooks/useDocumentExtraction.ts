import { useCallback, useState } from "react";
import { toast } from "sonner";
import { getApiErrorMessage } from "@/api/client";
import { getDocumentExtraction } from "@/api/documents";
import type { DocumentExtraction } from "@/types/api";

interface UseDocumentExtractionResult {
  extraction: DocumentExtraction | null;
  isLoading: boolean;
  load: (sessionId: string, documentId: string) => Promise<void>;
  reset: () => void;
}

export function useDocumentExtraction(): UseDocumentExtractionResult {
  const [extraction, setExtraction] = useState<DocumentExtraction | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const load = useCallback(
    async (sessionId: string, documentId: string): Promise<void> => {
      setIsLoading(true);
      setExtraction(null);

      try {
        const result = await getDocumentExtraction(sessionId, documentId);

        setExtraction(result);
      } catch (error) {
        toast.error(
          getApiErrorMessage(error, "Unable to load document extraction."),
        );
      } finally {
        setIsLoading(false);
      }
    },
    [],
  );

  const reset = useCallback((): void => {
    setExtraction(null);
    setIsLoading(false);
  }, []);

  return {
    extraction,
    isLoading,
    load,
    reset,
  };
}
