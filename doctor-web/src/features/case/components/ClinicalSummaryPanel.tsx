import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ClinicalSummary } from "@/types/api";
import type { SummaryForm } from "@/features/case/hooks/useSummaryEditor";
import SummaryActions from "./summary/SummaryActions";
import SummaryEditor from "./summary/SummaryEditor";
import SummaryFields from "./summary/SummaryFields";

export default function ClinicalSummaryPanel({
  summary,
  isEditing,
  isSaving,
  isConfirming,
  form,
  setForm,
  onEdit,
  onSave,
  onCancel,
  onConfirm,
}: {
  summary: ClinicalSummary | null;
  isEditing: boolean;
  isSaving: boolean;
  isConfirming: boolean;
  form: SummaryForm;
  setForm: React.Dispatch<React.SetStateAction<SummaryForm>>;
  onEdit: () => void;
  onSave: () => void;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  const isConfirmed = summary?.status === "CONFIRMED";

  return (
    <Card className="rounded-[20px] border border-border bg-surface p-0 shadow-none">
      <CardHeader className="flex flex-row items-center justify-between gap-3 px-5.5 pb-0 pt-5">
        <CardTitle className="font-display text-[15.5px] font-semibold text-primary-dark">
          Clinical summary
        </CardTitle>

        {summary && (
          <span
            className="rounded-full px-2.5 py-0.75 text-[10.5px] font-extrabold"
            style={{
              background: isConfirmed
                ? "color-mix(in srgb, var(--aurora-success) 20%, var(--aurora-surface))"
                : "var(--aurora-primary-tint)",
              color: isConfirmed
                ? "color-mix(in srgb, var(--aurora-success) 55%, var(--aurora-text-primary))"
                : "var(--aurora-primary-dark)",
            }}
          >
            {isConfirmed ? "Confirmed" : "AI-generated"}
          </span>
        )}
      </CardHeader>

      <CardContent className="px-5.5 pb-5 pt-3.5">
        {!summary ? (
          <span className="text-xs italic text-text-secondary">
            No clinical summary available.
          </span>
        ) : isEditing ? (
          <SummaryEditor form={form} setForm={setForm} />
        ) : (
          <SummaryFields summary={summary} />
        )}

        {summary && (
          <SummaryActions
            isConfirmed={isConfirmed}
            isConfirming={isConfirming}
            isEditing={isEditing}
            isSaving={isSaving}
            onCancel={onCancel}
            onConfirm={onConfirm}
            onEdit={onEdit}
            onSave={onSave}
          />
        )}
      </CardContent>
    </Card>
  );
}
