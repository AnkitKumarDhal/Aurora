import {
  AlertTriangle,
  CheckCircle2,
  FileText,
  LoaderCircle,
  ShieldAlert,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { DoctorCaseDocument, DocumentExtraction } from "@/types/api";

function formatDocumentType(documentType: string): string {
  return documentType
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatLabel(value: string): string {
  return value
    .replace(/_/g, " ")
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatScalar(value: unknown): string {
  if (value === null || value === undefined) {
    return "Not available";
  }

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  if (typeof value === "string" || typeof value === "number") {
    return String(value);
  }

  return JSON.stringify(value);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function ValueContent({ value }: { value: unknown }) {
  if (value === null || value === undefined) {
    return <span className="text-text-secondary">Not available</span>;
  }

  if (
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return (
      <span className="font-semibold text-text-primary">
        {formatScalar(value)}
      </span>
    );
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return <span className="text-text-secondary">None recorded</span>;
    }

    const primitiveArray = value.every(
      (item) =>
        item === null || ["string", "number", "boolean"].includes(typeof item),
    );

    if (primitiveArray) {
      return (
        <div className="flex flex-wrap gap-1.5">
          {value.map((item, index) => (
            <span
              className="rounded-full border border-border bg-surface px-2.5 py-1 text-[11px] font-semibold text-text-primary"
              key={`${String(item)}-${index}`}
            >
              {formatScalar(item)}
            </span>
          ))}
        </div>
      );
    }

    return (
      <div className="space-y-2">
        {value.map((item, index) => (
          <div
            className="rounded-lg border border-border bg-surface px-3 py-2"
            key={index}
          >
            <ValueContent value={item} />
          </div>
        ))}
      </div>
    );
  }

  if (isRecord(value)) {
    const entries = Object.entries(value);

    if (entries.length === 0) {
      return <span className="text-text-secondary">None recorded</span>;
    }

    return (
      <div className="grid gap-2 sm:grid-cols-2">
        {entries.map(([key, nestedValue]) => (
          <div
            className="rounded-lg border border-border bg-surface px-3 py-2.5"
            key={key}
          >
            <p className="text-[10.5px] font-bold uppercase tracking-wide text-text-secondary">
              {formatLabel(key)}
            </p>

            <div className="mt-1 text-[12px]">
              <ValueContent value={nestedValue} />
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <span className="font-semibold text-text-primary">
      {formatScalar(value)}
    </span>
  );
}

function ExtractionFields({ extraction }: { extraction: DocumentExtraction }) {
  const data = extraction.structured_data;

  if (!data) {
    return (
      <div className="rounded-xl border border-border bg-surface-alt px-4 py-4 text-xs text-text-secondary">
        No structured information was extracted.
      </div>
    );
  }

  const nestedStructured = isRecord(data.structured) ? data.structured : null;

  const fallbackData = Object.fromEntries(
    Object.entries(data).filter(
      ([key]) =>
        ![
          "structured",
          "raw_text",
          "ocr",
          "document_summary",
          "medication_safety",
          "review_reasons",
          "manual_review_required",
        ].includes(key),
    ),
  );

  const fields =
    nestedStructured && Object.keys(nestedStructured).length > 0
      ? nestedStructured
      : fallbackData;

  if (Object.keys(fields).length === 0) {
    return (
      <div className="rounded-xl border border-border bg-surface-alt px-4 py-4 text-xs text-text-secondary">
        No structured information was extracted.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {Object.entries(fields).map(([key, value]) => (
        <div
          className="rounded-xl border border-border bg-surface-alt px-3.5 py-3"
          key={key}
        >
          <p className="mb-1.5 text-[10.5px] font-bold uppercase tracking-wide text-text-secondary">
            {formatLabel(key)}
          </p>

          <ValueContent value={value} />
        </div>
      ))}
    </div>
  );
}

function ReviewStatus({ extraction }: { extraction: DocumentExtraction }) {
  const data = extraction.structured_data;

  if (!data) {
    return null;
  }

  const manualReviewRequired = data.manual_review_required === true;

  const reasons = Array.isArray(data.review_reasons)
    ? data.review_reasons.filter(
        (reason): reason is string => typeof reason === "string",
      )
    : [];

  return (
    <div
      className="rounded-xl border px-3.5 py-3"
      style={{
        borderColor: manualReviewRequired
          ? "color-mix(in srgb, var(--aurora-warning) 45%, var(--aurora-border))"
          : "color-mix(in srgb, var(--aurora-success) 35%, var(--aurora-border))",
        background: manualReviewRequired
          ? "color-mix(in srgb, var(--aurora-warning) 10%, var(--aurora-surface))"
          : "color-mix(in srgb, var(--aurora-success) 9%, var(--aurora-surface))",
      }}
    >
      <div className="flex items-start gap-2.5">
        {manualReviewRequired ? (
          <ShieldAlert className="mt-0.5 size-4 shrink-0 text-warning" />
        ) : (
          <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-success" />
        )}

        <div className="min-w-0">
          <p className="text-[12px] font-bold text-text-primary">
            {manualReviewRequired
              ? "Manual verification recommended"
              : "No manual review flag raised"}
          </p>

          {reasons.length > 0 && (
            <ul className="mt-1.5 space-y-1">
              {reasons.map((reason) => (
                <li className="text-[11px] text-text-secondary" key={reason}>
                  {reason}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

function SourceViewer({
  document,
  fileUrl,
}: {
  document: DoctorCaseDocument;
  fileUrl: string | null;
}) {
  const isPdf =
    document.content_type === "application/pdf" ||
    document.filename.toLowerCase().endsWith(".pdf");

  if (!fileUrl) {
    return (
      <div className="flex h-full min-h-90 items-center justify-center rounded-xl border border-border bg-surface-alt">
        <div className="px-6 text-center">
          <FileText className="mx-auto mb-3 size-8 text-text-secondary" />

          <p className="text-[13px] font-bold text-text-primary">
            Original document unavailable
          </p>

          <p className="mt-1 text-[11px] text-text-secondary">
            The stored source file could not be loaded.
          </p>
        </div>
      </div>
    );
  }

  if (isPdf) {
    return (
      <iframe
        className="h-full min-h-110 w-full rounded-xl border border-border bg-white"
        src={fileUrl}
        title={`Original ${document.filename}`}
      />
    );
  }

  if (document.content_type.startsWith("image/")) {
    return (
      <div className="flex h-full min-h-110 items-center justify-center overflow-auto rounded-xl border border-border bg-black/5 p-3">
        <img
          alt={`Original ${document.filename}`}
          className="max-h-full max-w-full rounded-lg object-contain"
          src={fileUrl}
        />
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-90 items-center justify-center rounded-xl border border-border bg-surface-alt px-6 text-center">
      <div>
        <FileText className="mx-auto mb-3 size-8 text-text-secondary" />

        <p className="text-[13px] font-bold text-text-primary">
          Preview unavailable
        </p>

        <p className="mt-1 text-[11px] text-text-secondary">
          The original file type cannot be previewed here.
        </p>
      </div>
    </div>
  );
}

function ExtractionContent({
  document,
  extraction,
  fileUrl,
  isLoading,
}: {
  document: DoctorCaseDocument;
  extraction: DocumentExtraction | null;
  fileUrl: string | null;
  isLoading: boolean;
}) {
  return (
    <div className="grid min-h-125 gap-4 lg:grid-cols-[minmax(0,0.9fr)_minmax(420px,1.1fr)]">
      <div className="grid min-h-0 gap-4 lg:grid-rows-[minmax(0,1fr)_minmax(0,1fr)]">
        <section className="flex min-h-0 flex-col overflow-hidden rounded-xl border border-border bg-surface">
          <div className="border-b border-border px-4 py-3">
            <p className="text-[12px] font-bold text-primary-dark">
              Extracted information
            </p>

            <p className="mt-0.5 text-[10.5px] text-text-secondary">
              Structured values detected from the source.
            </p>
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto p-3.5">
            {isLoading && !extraction ? (
              <div className="flex min-h-45 items-center justify-center">
                <div className="flex items-center gap-2 text-xs font-semibold text-text-secondary">
                  <LoaderCircle className="size-4 animate-spin" />
                  Loading extracted information
                </div>
              </div>
            ) : extraction ? (
              <div className="space-y-3">
                <ReviewStatus extraction={extraction} />

                <div className="grid gap-2 sm:grid-cols-2">
                  {[
                    [
                      "Document type",
                      formatDocumentType(document.document_type),
                    ],
                    [
                      "Patient name",
                      getStructuredMetadata(extraction, "patient_name"),
                    ],
                    [
                      "Document date",
                      getStructuredMetadata(extraction, "date"),
                    ],
                    ["OCR confidence", getOcrConfidence(extraction)],
                  ].map(([label, value]) => (
                    <div
                      className="rounded-lg border border-border bg-surface-alt px-3 py-2.5"
                      key={label}
                    >
                      <p className="text-[10px] font-bold uppercase tracking-wide text-text-secondary">
                        {label}
                      </p>

                      <p className="mt-1 text-[12px] font-semibold text-text-primary">
                        {value}
                      </p>
                    </div>
                  ))}
                </div>

                <ExtractionFields extraction={extraction} />
              </div>
            ) : (
              <div className="flex min-h-45 items-center justify-center text-center">
                <div>
                  <AlertTriangle className="mx-auto mb-3 size-7 text-warning" />

                  <p className="text-[13px] font-bold text-text-primary">
                    No extraction available
                  </p>

                  <p className="mt-1 text-[11px] text-text-secondary">
                    Structured information has not been generated yet.
                  </p>
                </div>
              </div>
            )}
          </div>
        </section>

        <section className="flex min-h-0 flex-col overflow-hidden rounded-xl border border-border bg-surface">
          <div className="border-b border-border px-4 py-3">
            <p className="text-[12px] font-bold text-primary-dark">
              Raw OCR extraction
            </p>

            <p className="mt-0.5 text-[10.5px] text-text-secondary">
              Original machine-read text. Verify important values against the
              source.
            </p>
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto p-3.5">
            {extraction?.extracted_text ? (
              <div className="whitespace-pre-wrap rounded-xl border border-border bg-surface-alt px-3.5 py-3 text-[11.5px] leading-[1.65] text-text-primary">
                {extraction.extracted_text}
              </div>
            ) : (
              <div className="flex min-h-35 items-center justify-center text-center text-[11px] text-text-secondary">
                No raw OCR text is available.
              </div>
            )}
          </div>
        </section>
      </div>

      <section className="flex min-h-0 flex-col overflow-hidden rounded-xl border border-border bg-surface">
        <div className="flex items-center justify-between gap-3 border-b border-border px-4 py-3">
          <div>
            <p className="text-[12px] font-bold text-primary-dark">
              Original document
            </p>

            <p className="mt-0.5 truncate text-[10.5px] text-text-secondary">
              {document.filename}
            </p>
          </div>

          <span className="shrink-0 rounded-full bg-primary-tint px-2.5 py-1 text-[10px] font-extrabold text-primary-dark">
            Source
          </span>
        </div>

        <div className="min-h-0 flex-1 p-3.5">
          <SourceViewer document={document} fileUrl={fileUrl} />
        </div>
      </section>
    </div>
  );
}

function getStructuredMetadata(
  extraction: DocumentExtraction,
  key: string,
): string {
  const data = extraction.structured_data;

  if (!data) {
    return "Not available";
  }

  const directValue = data[key];

  if (typeof directValue === "string" || typeof directValue === "number") {
    return String(directValue);
  }

  if (
    isRecord(data.structured) &&
    (typeof data.structured[key] === "string" ||
      typeof data.structured[key] === "number")
  ) {
    return String(data.structured[key]);
  }

  return "Not available";
}

function getOcrConfidence(extraction: DocumentExtraction): string {
  const data = extraction.structured_data;

  if (!data || !isRecord(data.ocr)) {
    return "Not available";
  }

  const confidence = data.ocr.mean_confidence;

  if (typeof confidence !== "number") {
    return "Not available";
  }

  return `${Math.round(confidence * 100)}%`;
}

export default function DocumentExtractionDialog({
  document,
  extraction,
  fileUrl,
  isLoading,
  open,
  onOpenChange,
}: {
  document: DoctorCaseDocument | null;
  extraction: DocumentExtraction | null;
  fileUrl: string | null;
  isLoading: boolean;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[92vh] max-w-330 overflow-hidden rounded-[20px] border-border bg-surface p-0">
        <DialogHeader className="border-b border-border px-6 py-4.5">
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
                  ? `${formatDocumentType(
                      document.document_type,
                    )} · original source + OCR review`
                  : "Document details"}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="min-h-0 overflow-y-auto px-5 py-4.5">
          {document ? (
            <ExtractionContent
              document={document}
              extraction={extraction}
              fileUrl={fileUrl}
              isLoading={isLoading}
            />
          ) : null}
        </div>
      </DialogContent>
    </Dialog>
  );
}
