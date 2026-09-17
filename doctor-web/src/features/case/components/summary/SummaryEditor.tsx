import type { Dispatch, SetStateAction } from "react";
import type { SummaryForm } from "@/features/case/hooks/useSummaryEditor";

export default function SummaryEditor({
  form,
  setForm,
}: {
  form: SummaryForm;
  setForm: Dispatch<SetStateAction<SummaryForm>>;
}) {
  return (
    <div className="space-y-4">
      <div>
        <label
          className="mb-1.5 block text-[11.5px] font-bold text-text-secondary"
          htmlFor="edit-chief-complaint"
        >
          Chief complaint
        </label>

        <input
          className="w-full rounded-lg border border-border bg-surface-alt px-3 py-2.5 text-sm text-text-primary outline-none transition focus:border-primary focus:ring-2 focus:ring-primary-tint"
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

      <div>
        <label
          className="mb-1.5 block text-[11.5px] font-bold text-text-secondary"
          htmlFor="edit-hpi"
        >
          History of present illness
        </label>

        <textarea
          className="min-h-28 w-full resize-y rounded-lg border border-border bg-surface-alt px-3 py-2.5 text-sm leading-[1.55] text-text-primary outline-none transition focus:border-primary focus:ring-2 focus:ring-primary-tint"
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

      <div>
        <label
          className="mb-1.5 block text-[11.5px] font-bold text-text-secondary"
          htmlFor="edit-pmh"
        >
          Past medical history
        </label>

        <input
          className="w-full rounded-lg border border-border bg-surface-alt px-3 py-2.5 text-sm text-text-primary outline-none transition focus:border-primary focus:ring-2 focus:ring-primary-tint"
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

      <div>
        <label
          className="mb-1.5 block text-[11.5px] font-bold text-text-secondary"
          htmlFor="edit-medications"
        >
          Medications
        </label>

        <input
          className="w-full rounded-lg border border-border bg-surface-alt px-3 py-2.5 text-sm text-text-primary outline-none transition focus:border-primary focus:ring-2 focus:ring-primary-tint"
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
          className="w-full rounded-lg border border-border bg-surface-alt px-3 py-2.5 text-sm text-text-primary outline-none transition focus:border-primary focus:ring-2 focus:ring-primary-tint"
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
