import type { ClinicalSummary } from "@/types/api";

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

export default function SummaryFields({
  summary,
}: {
  summary: ClinicalSummary;
}) {
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
