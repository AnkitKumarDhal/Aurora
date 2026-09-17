import { FileText } from "lucide-react";
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DoctorCaseDocument, DoctorCaseResponse } from "@/types/api";
import DocumentExtractionDialog from "./DocumentExtractionDialog";
import { useDocumentExtraction } from "../hooks/useDocumentExtraction";

function getStatusStyle(status: DoctorCaseDocument["status"]): {
  background: string;
  color: string;
} {
  switch (status) {
    case "PROCESSED":
      return {
        background:
          "color-mix(in srgb, var(--aurora-success) 18%, var(--aurora-surface))",
        color:
          "color-mix(in srgb, var(--aurora-success) 55%, var(--aurora-text-primary))",
      };
    case "FAILED":
      return {
        background:
          "color-mix(in srgb, var(--aurora-danger) 16%, var(--aurora-surface))",
        color: "var(--aurora-danger)",
      };
    case "PROCESSING":
      return {
        background:
          "color-mix(in srgb, var(--aurora-warning) 20%, var(--aurora-surface))",
        color:
          "color-mix(in srgb, var(--aurora-warning) 60%, var(--aurora-text-primary))",
      };
    default:
      return {
        background: "var(--aurora-accent-tint)",
        color: "var(--aurora-accent-dark)",
      };
  }
}

export default function DocumentsPanel({
  documents,
}: {
  documents: DoctorCaseResponse["documents"];
}) {
  const [selectedDocument, setSelectedDocument] =
    useState<DoctorCaseDocument | null>(null);
  const { extraction, isLoading, load, reset } = useDocumentExtraction();

  function handleDocumentOpen(document: DoctorCaseDocument): void {
    setSelectedDocument(document);
    void load(document.session_id, document.document_id);
  }

  function handleDialogChange(open: boolean): void {
    if (open) {
      return;
    }

    setSelectedDocument(null);
    reset();
  }

  return (
    <>
      <Card className="mt-4 rounded-[20px] border border-border bg-surface p-0 shadow-none">
        <CardHeader className="flex flex-row items-center justify-between px-5.5 pb-0 pt-5">
          <CardTitle className="font-display text-[15.5px] font-semibold text-primary-dark">
            Documents
          </CardTitle>

          <span className="text-[11.5px] text-text-secondary">
            {documents.length} {documents.length === 1 ? "file" : "files"}
          </span>
        </CardHeader>

        <CardContent className="px-5.5 pb-5 pt-3.5">
          {documents.length === 0 ? (
            <span className="text-xs italic text-text-secondary">
              No documents uploaded for this session
            </span>
          ) : (
            <div className="flex flex-col gap-2">
              {documents.map((document) => {
                const statusStyle = getStatusStyle(document.status);

                return (
                  <button
                    className="flex w-full items-center gap-2.5 rounded-md border border-border bg-surface-alt px-3 py-2.5 text-left transition hover:border-primary/60 hover:bg-primary-tint/20"
                    key={document.document_id}
                    onClick={() => handleDocumentOpen(document)}
                    type="button"
                  >
                    <span className="flex size-7.5 shrink-0 items-center justify-center rounded-lg bg-primary-tint text-primary-dark">
                      <FileText className="size-3.75" />
                    </span>

                    <div className="min-w-0 flex-1">
                      <p className="truncate text-[13px] font-bold text-text-primary">
                        {document.filename}
                      </p>

                      <p className="text-[11px] text-text-secondary">
                        {document.document_type
                          .replace(/_/g, " ")
                          .toLowerCase()}
                      </p>
                    </div>

                    <span
                      className="shrink-0 rounded-full px-2.25 py-0.75 text-[10.5px] font-extrabold"
                      style={statusStyle}
                    >
                      {document.status.toLowerCase()}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      <DocumentExtractionDialog
        document={selectedDocument}
        extraction={extraction}
        isLoading={isLoading}
        onOpenChange={handleDialogChange}
        open={selectedDocument !== null}
      />
    </>
  );
}
