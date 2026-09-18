import { FileText, LoaderCircle } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { DoctorCaseDocument, DocumentExtraction } from "@/types/api";

function formatDocumentType(documentType: string): string {
  return documentType.replace(/_/g, " ").toLowerCase();
}

function formatProcessedAt(value: string | null): string {
  if (!value) {
    return "Not processed";
  }

  return new Date(value).toLocaleString("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function ExtractionContent({
  document,
  extraction,
  isLoading,
}: {
  document: DoctorCaseDocument;
  extraction: DocumentExtraction | null;
  isLoading: boolean;
}) {
  if (isLoading) {
    return (
      <div className="flex min-h-55 items-center justify-center">
        <div className="flex items-center gap-2 text-xs font-semibold text-text-secondary">
          <LoaderCircle className="size-4 animate-spin" />
          Loading extracted information
        </div>
      </div>
    );
  }

  if (document.status === "PROCESSING") {
    return (
      <div className="flex min-h-55 items-center justify-center text-center">
        <div>
          <p className="text-sm font-bold text-text-primary">
            Document is still being processed
          </p>
          <p className="mt-1 text-xs text-text-secondary">
            Extracted information will appear here when processing is complete.
          </p>
        </div>
      </div>
    );
  }

  if (document.status === "FAILED") {
    return (
      <div className="flex min-h-55 items-center justify-center text-center">
        <div>
          <p className="text-sm font-bold text-danger">
            Document processing failed
          </p>
          <p className="mt-1 text-xs text-text-secondary">
            No extracted information is available for this document.
          </p>
        </div>
      </div>
    );
  }

  if (!extraction) {
    return (
      <div className="flex min-h-55 items-center justify-center text-center">
        <div>
          <p className="text-sm font-bold text-text-primary">
            No extraction available
          </p>
          <p className="mt-1 text-xs text-text-secondary">
            This document does not have extracted information yet.
          </p>
        </div>
      </div>
    );
  }

  const structuredData = extraction.structured_data
    ? JSON.stringify(extraction.structured_data, null, 2)
    : null;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-4 rounded-lg border border-border bg-surface-alt px-3.5 py-3">
        <div>
          <p className="text-xs font-bold text-text-primary">
            Processing status
          </p>

          <p className="mt-0.5 text-[11px] text-text-secondary">
            {extraction.status.toLowerCase()}
          </p>
        </div>

        <span className="text-right text-[11px] text-text-secondary">
          {formatProcessedAt(extraction.processed_at)}
        </span>
      </div>

      {extraction.extracted_text && (
        <section>
          <h3 className="mb-2 text-[12px] font-bold text-primary-dark">
            Extracted text
          </h3>

          <div className="max-h-80 overflow-auto whitespace-pre-wrap rounded-lg border border-border bg-surface-alt px-3.5 py-3 text-[12.5px] leading-[1.6] text-text-primary">
            {extraction.extracted_text}
          </div>
        </section>
      )}

      {structuredData && (
        <section>
          <h3 className="mb-2 text-[12px] font-bold text-primary-dark">
            Structured information
          </h3>

          <pre className="max-h-75 overflow-auto rounded-lg border border-border bg-surface-alt px-3.5 py-3 text-[11.5px] leading-[1.55] text-text-primary">
            {structuredData}
          </pre>
        </section>
      )}
    </div>
  );
}

export default function DocumentExtractionDialog({
  document,
  extraction,
  isLoading,
  open,
  onOpenChange,
}: {
  document: DoctorCaseDocument | null;
  extraction: DocumentExtraction | null;
  isLoading: boolean;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] max-w-180 overflow-hidden rounded-[20px] border-border bg-surface p-0">
        <DialogHeader className="border-b border-border px-6 py-5">
          <div className="flex items-start gap-3">
            <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-primary-tint text-primary-dark">
              <FileText className="size-4.5" />
            </span>

            <div className="min-w-0">
              <DialogTitle className="truncate pr-4 font-display text-[17px] font-semibold text-primary-dark">
                {document?.filename ?? "Document"}
              </DialogTitle>

              <DialogDescription className="mt-1 text-[11.5px] text-text-secondary">
                {document
                  ? formatDocumentType(document.document_type)
                  : "Document details"}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="overflow-y-auto px-6 py-5">
          {document ? (
            <ExtractionContent
              document={document}
              extraction={extraction}
              isLoading={isLoading}
            />
          ) : null}
        </div>
      </DialogContent>
    </Dialog>
  );
}
