import { useCallback, useRef, useState } from "react";
import { toast } from "sonner";
import { getApiErrorMessage } from "@/api/client";
import { getDocumentExtraction, getDocumentFile } from "@/api/documents";
import type { DocumentExtraction } from "@/types/api";

interface UseDocumentExtractionResult {
  extraction: DocumentExtraction | null;
  fileUrl: string | null;
  isLoading: boolean;
  load: (sessionId: string, documentId: string) => Promise<void>;
  reset: () => void;
}

export function useDocumentExtraction(): UseDocumentExtractionResult {
  const [extraction, setExtraction] = useState<DocumentExtraction | null>(null);

  const [fileUrl, setFileUrl] = useState<string | null>(null);

  const [isLoading, setIsLoading] = useState(false);

  const requestIdRef = useRef(0);

  const load = useCallback(
    async (sessionId: string, documentId: string): Promise<void> => {
      const requestId = requestIdRef.current + 1;

      requestIdRef.current = requestId;

      setIsLoading(true);
      setExtraction(null);

      setFileUrl((current) => {
        if (current) {
          URL.revokeObjectURL(current);
        }

        return null;
      });

      const [extractionResult, fileResult] = await Promise.allSettled([
        getDocumentExtraction(sessionId, documentId),
        getDocumentFile(sessionId, documentId),
      ]);

      if (requestIdRef.current !== requestId) {
        return;
      }

      if (extractionResult.status === "fulfilled") {
        setExtraction(extractionResult.value);
      } else {
        toast.error(
          getApiErrorMessage(
            extractionResult.reason,
            "Unable to load document extraction.",
          ),
        );
      }

      if (fileResult.status === "fulfilled") {
        setFileUrl(URL.createObjectURL(fileResult.value));
      } else {
        toast.error(
          getApiErrorMessage(
            fileResult.reason,
            "Unable to load the original document.",
          ),
        );
      }

      setIsLoading(false);
    },
    [],
  );

  const reset = useCallback(() => {
    requestIdRef.current += 1;

    setExtraction(null);

    setFileUrl((current) => {
      if (current) {
        URL.revokeObjectURL(current);
      }

      return null;
    });

    setIsLoading(false);
  }, []);

  return {
    extraction,
    fileUrl,
    isLoading,
    load,
    reset,
  };
}
