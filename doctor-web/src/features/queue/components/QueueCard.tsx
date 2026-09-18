import type { DoctorQueueEntry } from "@/types/api";
import { useElapsedSeconds } from "@/hooks/useElapsedSeconds";
import { getUrgencyStyles } from "@/lib/urgency";
import { formatWaitingTime, getQueueStatusStyles } from "../utils";

export default function QueueCard({
  entry,
  onOpen,
}: {
  entry: DoctorQueueEntry;
  onOpen: (entry: DoctorQueueEntry) => void;
}) {
  const severity = getUrgencyStyles(entry.urgency_level);
  const status = getQueueStatusStyles(entry.status);

  const waitingSeconds = useElapsedSeconds(
    entry.waiting_time_seconds,
    entry.queued_at,
    entry.status === "WAITING" || entry.status === "PROMOTION_PENDING",
  );

  return (
    <button
      className={`group relative flex min-h-[140px] flex-col overflow-hidden rounded-[14px] border border-border bg-surface p-[18px] pb-4 text-left shadow-[0_10px_24px_-18px_rgba(58,46,92,0.4)] transition duration-150 before:absolute before:inset-x-0 before:top-0 before:h-[5px] before:rounded-t-[14px] ${severity.accent} hover:-translate-y-[3px] hover:border-primary hover:shadow-[0_20px_32px_-18px_rgba(58,46,92,0.45)]`}
      onClick={() => onOpen(entry)}
      type="button"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-[15.5px] font-extrabold text-text-primary">
            {entry.patient?.display_name ?? "Unknown patient"}
          </p>

          <p className="mt-px text-xs text-text-secondary">
            {entry.patient?.age !== null && entry.patient?.age !== undefined
              ? `${entry.patient.age} yrs`
              : "Age unknown"}{" "}
            · position {entry.position ?? "—"}
          </p>
        </div>

        <span
          className="shrink-0 rounded-full px-[9px] py-[3px] text-[10.5px] font-extrabold"
          style={{
            background: severity.badgeBackground,
            color: severity.badgeColor,
          }}
        >
          Level {entry.urgency_level ?? "—"} · {severity.label}
        </span>
      </div>

      <p className="mb-3.5 mt-1 min-h-[2.6em] line-clamp-2 text-[13px] leading-[1.5] text-text-primary">
        {entry.summary?.chief_complaint ?? "No chief complaint available"}
      </p>

      <div className="mt-auto flex items-center justify-between">
        <span
          className="inline-flex items-center gap-[5px] rounded-full px-2.5 py-1 text-[11px] font-bold"
          style={{
            background: status.background,
            color: status.text,
          }}
        >
          <span
            className="size-1.5 rounded-full"
            style={{
              background: status.dot,
            }}
          />
          {status.label}
        </span>

        <span className="text-xs tabular-nums text-text-secondary">
          {formatWaitingTime(waitingSeconds)}
        </span>
      </div>
    </button>
  );
}
