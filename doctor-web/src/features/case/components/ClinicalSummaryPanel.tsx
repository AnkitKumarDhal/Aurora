import { LoaderCircle, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ClinicalSummary } from "@/types/api";

interface SummaryForm {
  chief_complaint: string;
  history_of_present_illness: string;
  past_medical_history: string;
  medications: string;
  allergies: string;
}

function TagList({
  items,
  muted = false,
}: {
  items: string[];
  muted?: boolean;
}) {
  if (items.length === 0) {
    return (
      <span className="text-xs italic text-text-secondary">None recorded</span>
    );
  }

  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((item) => (
        <span
          className={[
            "rounded-full px-2.5 py-1 text-xs font-semibold",
            muted
              ? "bg-primary-tint text-primary-dark"
              : "bg-accent-tint text-accent-dark",
          ].join(" ")}
          key={item}
        >
          {item}
        </span>
      ))}
    </div>
  );
}

function SummaryView({ summary }: { summary: ClinicalSummary }) {
  return (
    <div>
      <div className="mb-4">
        <div className="mb-1.5 text-[11.5px] font-bold text-text-secondary">
          Chief complaint
        </div>

        <div className="text-sm leading-[1.55]">
          {summary.chief_complaint ?? "—"}
        </div>
      </div>

      <div className="mb-4">
        <div className="mb-1.5 text-[11.5px] font-bold text-text-secondary">
          History of present illness
        </div>

        <div className="text-sm leading-[1.55]">
          {summary.history_of_present_illness ?? "—"}
        </div>
      </div>

      <div className="mb-4">
        <div className="mb-1.5 text-[11.5px] font-bold text-text-secondary">
          Past medical history
        </div>

        <TagList items={summary.past_medical_history} muted />
      </div>

      <div className="mb-4">
        <div className="mb-1.5 text-[11.5px] font-bold text-text-secondary">
          Medications
        </div>

        <TagList items={summary.medications} />
      </div>

      <div>
        <div className="mb-1.5 text-[11.5px] font-bold text-text-secondary">
          Allergies
        </div>

        <TagList items={summary.allergies} />
      </div>
    </div>
  );
}

function SummaryEdit({
  form,
  setForm,
}: {
  form: SummaryForm;
  setForm: React.Dispatch<React.SetStateAction<SummaryForm>>;
}) {
  return (
    <div>
      <div className="mb-4">
        <label
          className="mb-1.5 block text-[11.5px] font-bold text-text-secondary"
          htmlFor="edit-chief-complaint"
        >
          Chief complaint
        </label>

        <input
          className="w-full rounded-md border-[1.5px] border-border bg-surface-alt px-3 py-2 text-sm text-text-primary outline-none focus:border-primary focus:ring-2 focus:ring-primary-tint"
          id="edit-chief-complaint"
          onChange={(event) =>
            setForm((current) => ({
              ...current,
              chief_complaint: event.target.value,
            }))
          }
          value={form.chief_complaint}
        />
      </div>

      <div className="mb-4">
        <label
          className="mb-1.5 block text-[11.5px] font-bold text-text-secondary"
          htmlFor="edit-hpi"
        >
          History of present illness
        </label>

        <textarea
          className="min-h-24 w-full resize-y rounded-md border-[1.5px] border-border bg-surface-alt px-3 py-2 text-sm leading-[1.55] text-text-primary outline-none focus:border-primary focus:ring-2 focus:ring-primary-tint"
          id="edit-hpi"
          onChange={(event) =>
            setForm((current) => ({
              ...current,
              history_of_present_illness: event.target.value,
            }))
          }
          value={form.history_of_present_illness}
        />
      </div>

      <div className="mb-4">
        <label
          className="mb-1.5 block text-[11.5px] font-bold text-text-secondary"
          htmlFor="edit-pmh"
        >
          Past medical history
        </label>

        <input
          className="w-full rounded-md border-[1.5px] border-border bg-surface-alt px-3 py-2 text-sm text-text-primary outline-none focus:border-primary focus:ring-2 focus:ring-primary-tint"
          id="edit-pmh"
          onChange={(event) =>
            setForm((current) => ({
              ...current,
              past_medical_history: event.target.value,
            }))
          }
          placeholder="Separate items with commas"
          value={form.past_medical_history}
        />
      </div>

      <div className="mb-4">
        <label
          className="mb-1.5 block text-[11.5px] font-bold text-text-secondary"
          htmlFor="edit-medications"
        >
          Medications
        </label>

        <input
          className="w-full rounded-md border-[1.5px] border-border bg-surface-alt px-3 py-2 text-sm text-text-primary outline-none focus:border-primary focus:ring-2 focus:ring-primary-tint"
          id="edit-medications"
          onChange={(event) =>
            setForm((current) => ({
              ...current,
              medications: event.target.value,
            }))
          }
          placeholder="Separate items with commas"
          value={form.medications}
        />
      </div>

      <div>
        <label
          className="mb-1.5 block text-[11.5px] font-bold text-text-secondary"
          htmlFor="edit-allergies"
        >
          Allergies
        </label>

        <input
          className="w-full rounded-md border-[1.5px] border-border bg-surface-alt px-3 py-2 text-sm text-text-primary outline-none focus:border-primary focus:ring-2 focus:ring-primary-tint"
          id="edit-allergies"
          onChange={(event) =>
            setForm((current) => ({
              ...current,
              allergies: event.target.value,
            }))
          }
          placeholder="Separate items with commas"
          value={form.allergies}
        />
      </div>
    </div>
  );
}

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
  return (
    <Card className="rounded-[20px] border border-border bg-surface p-0 shadow-none">
      <CardHeader className="flex flex-row items-center justify-between gap-3 px-[22px] pb-0 pt-5">
        <CardTitle className="font-display text-[15.5px] font-semibold text-primary-dark">
          Clinical summary
        </CardTitle>

        {summary && (
          <span
            className="rounded-full px-[9px] py-[3px] text-[10.5px] font-extrabold"
            style={{
              background:
                summary.status === "CONFIRMED"
                  ? "color-mix(in srgb, var(--aurora-success) 20%, var(--aurora-surface))"
                  : "var(--aurora-primary-tint)",
              color:
                summary.status === "CONFIRMED"
                  ? "color-mix(in srgb, var(--aurora-success) 55%, var(--aurora-text-primary))"
                  : "var(--aurora-primary-dark)",
            }}
          >
            {summary.status === "CONFIRMED" ? "Confirmed" : "AI-generated"}
          </span>
        )}
      </CardHeader>

      <CardContent className="px-[22px] pb-5 pt-[14px]">
        {!summary ? (
          <span className="text-xs italic text-text-secondary">
            No clinical summary available.
          </span>
        ) : isEditing ? (
          <SummaryEdit form={form} setForm={setForm} />
        ) : (
          <SummaryView summary={summary} />
        )}

        {summary && (
          <div className="mt-[18px] flex gap-2 border-t border-border pt-4">
            {isEditing ? (
              <>
                <Button
                  className="h-9 rounded-md border border-primary bg-primary-tint px-4 text-xs font-bold text-primary-dark hover:bg-primary-tint"
                  disabled={isSaving}
                  onClick={onSave}
                  type="button"
                  variant="outline"
                >
                  {isSaving ? (
                    <>
                      <LoaderCircle className="size-4 animate-spin" />
                      Saving
                    </>
                  ) : (
                    "Save changes"
                  )}
                </Button>

                <Button
                  className="h-9 rounded-md px-4 text-xs font-bold text-text-secondary"
                  disabled={isSaving}
                  onClick={onCancel}
                  type="button"
                  variant="ghost"
                >
                  Cancel
                </Button>
              </>
            ) : (
              <>
                <Button
                  className="h-9 rounded-md border border-border bg-surface-alt px-4 text-xs font-bold text-text-secondary hover:bg-primary-tint hover:text-primary-dark"
                  onClick={onEdit}
                  type="button"
                  variant="outline"
                >
                  Edit summary
                </Button>

                <Button
                  className="h-9 flex-1 rounded-md bg-primary-dark text-xs font-bold text-surface hover:bg-primary-dark/90"
                  disabled={isConfirming || summary.status === "CONFIRMED"}
                  onClick={onConfirm}
                  type="button"
                >
                  {isConfirming ? (
                    <>
                      <LoaderCircle className="size-4 animate-spin" />
                      Confirming
                    </>
                  ) : summary.status === "CONFIRMED" ? (
                    <>
                      <Check className="size-4" />
                      Summary confirmed
                    </>
                  ) : (
                    "Confirm summary"
                  )}
                </Button>
              </>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
