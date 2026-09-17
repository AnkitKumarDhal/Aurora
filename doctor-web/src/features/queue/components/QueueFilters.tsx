import { Button } from "@/components/ui/button";

export type QueueFilter =
  | "ALL"
  | "WAITING"
  | "PROMOTION_PENDING"
  | "CALLED"
  | "IN_CONSULTATION";

const QUEUE_FILTERS: {
  value: QueueFilter;
  label: string;
}[] = [
  {
    value: "ALL",
    label: "All",
  },
  {
    value: "WAITING",
    label: "Waiting",
  },
  {
    value: "PROMOTION_PENDING",
    label: "Promotion review",
  },
  {
    value: "CALLED",
    label: "Called",
  },
  {
    value: "IN_CONSULTATION",
    label: "In consultation",
  },
];

export default function QueueFilters({
  value,
  counts,
  onChange,
}: {
  value: QueueFilter;
  counts: Record<QueueFilter, number>;
  onChange: (value: QueueFilter) => void;
}) {
  return (
    <div className="my-[22px] flex flex-wrap gap-2">
      {QUEUE_FILTERS.map((option) => {
        const active = value === option.value;

        return (
          <Button
            className={[
              "h-auto rounded-full border-[1.5px] px-3.5 py-[7px] text-xs font-bold shadow-none",
              active
                ? "border-primary-dark bg-primary-dark text-surface-alt hover:bg-primary-dark"
                : "border-border bg-surface-alt text-text-secondary hover:border-primary hover:bg-surface-alt hover:text-primary-dark",
            ].join(" ")}
            key={option.value}
            onClick={() => onChange(option.value)}
            type="button"
            variant="outline"
          >
            {option.label}

            <span
              className={[
                "rounded-full px-1.5 py-px text-[11px]",
                active
                  ? "bg-white/20 text-white"
                  : "bg-border text-text-primary",
              ].join(" ")}
            >
              {counts[option.value]}
            </span>
          </Button>
        );
      })}
    </div>
  );
}
