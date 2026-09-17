import { FileText } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DoctorCaseResponse } from "@/types/api";

export default function DocumentsPanel({
  documents,
}: {
  documents: DoctorCaseResponse["documents"];
}) {
  return (
    <Card className="mt-4 rounded-[20px] border border-border bg-surface p-0 shadow-none">
      <CardHeader className="flex flex-row items-center justify-between px-[22px] pb-0 pt-5">
        <CardTitle className="font-display text-[15.5px] font-semibold text-primary-dark">
          Documents
        </CardTitle>

        <span className="text-[11.5px] text-text-secondary">
          {documents.length} {documents.length === 1 ? "file" : "files"}
        </span>
      </CardHeader>

      <CardContent className="px-[22px] pb-5 pt-[14px]">
        {documents.length === 0 ? (
          <span className="text-xs italic text-text-secondary">
            No documents uploaded for this session
          </span>
        ) : (
          <div className="flex flex-col gap-2">
            {documents.map((document) => {
              const processed = document.status === "PROCESSED";
              const failed = document.status === "FAILED";

              return (
                <div
                  className="flex items-center gap-2.5 rounded-md border border-border bg-surface-alt px-3 py-2.5"
                  key={document.document_id}
                >
                  <span className="flex size-[30px] shrink-0 items-center justify-center rounded-lg bg-primary-tint text-primary-dark">
                    <FileText className="size-[15px]" />
                  </span>

                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[13px] font-bold text-text-primary">
                      {document.filename}
                    </p>

                    <p className="text-[11px] text-text-secondary">
                      {document.document_type.replace(/_/g, " ").toLowerCase()}
                    </p>
                  </div>

                  <span
                    className="shrink-0 rounded-full px-[9px] py-[3px] text-[10.5px] font-extrabold"
                    style={{
                      background: processed
                        ? "color-mix(in srgb, var(--aurora-success) 18%, var(--aurora-surface))"
                        : failed
                          ? "color-mix(in srgb, var(--aurora-danger) 16%, var(--aurora-surface))"
                          : "var(--aurora-accent-tint)",
                      color: processed
                        ? "color-mix(in srgb, var(--aurora-success) 55%, var(--aurora-text-primary))"
                        : failed
                          ? "var(--aurora-danger)"
                          : "var(--aurora-accent-dark)",
                    }}
                  >
                    {document.status.toLowerCase()}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
