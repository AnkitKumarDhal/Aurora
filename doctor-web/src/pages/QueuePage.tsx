import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import DoctorHeader from "@/components/layout/DoctorHeader";
import { useAuth } from "@/auth/useAuth";
import { getDoctorQueue } from "@/api/queue";
import type { DoctorQueueEntry, QueueStatus } from "@/types/api";
import { useElapsedSeconds } from "@/hooks/useElapsedSeconds";
import { getUrgencyStyles } from "@/lib/urgency";

type QueueFilter =
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

function statusMeta(status: QueueStatus): {
  background: string;
  text: string;
  dot: string;
  label: string;
} {
  switch (status) {
    case "WAITING":
      return {
        background: "var(--aurora-primary-tint)",
        text: "var(--aurora-primary-dark)",
        dot: "var(--aurora-primary)",
        label: "Waiting",
      };
    case "PROMOTION_PENDING":
      return {
        background:
          "color-mix(in srgb, var(--aurora-warning) 22%, var(--aurora-surface))",
        text: "color-mix(in srgb, var(--aurora-warning) 60%, var(--aurora-text-primary))",
        dot: "var(--aurora-warning)",
        label: "Promotion review",
      };
    case "CALLED":
      return {
        background: "var(--aurora-accent-tint)",
        text: "var(--aurora-accent-dark)",
        dot: "var(--aurora-accent)",
        label: "Called",
      };
    case "IN_CONSULTATION":
      return {
        background:
          "color-mix(in srgb, var(--aurora-success) 18%, var(--aurora-surface))",
        text: "color-mix(in srgb, var(--aurora-success) 55%, var(--aurora-text-primary))",
        dot: "var(--aurora-success)",
        label: "In consultation",
      };
    case "COMPLETED":
      return {
        background: "var(--aurora-border)",
        text: "var(--aurora-text-secondary)",
        dot: "var(--aurora-text-secondary)",
        label: "Completed",
      };
    case "CANCELLED":
      return {
        background: "var(--aurora-primary-tint)",
        text: "var(--aurora-text-secondary)",
        dot: "var(--aurora-text-secondary)",
        label: "Cancelled",
      };
    default:
      return {
        background: "var(--aurora-primary-tint)",
        text: "var(--aurora-text-secondary)",
        dot: "var(--aurora-text-secondary)",
        label: status,
      };
  }
}

function formatWaitingTime(seconds: number | null): string {
  if (seconds === null) {
    return "—";
  }

  const totalMinutes = Math.floor(seconds / 60);
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;

  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }

  return `${minutes}m`;
}

function QueueCard({
  entry,
  onOpen,
}: {
  entry: DoctorQueueEntry;
  onOpen: (entry: DoctorQueueEntry) => void;
}) {
  const severity = getUrgencyStyles(entry.urgency_level);
  const status = statusMeta(entry.status);
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

export default function QueuePage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [entries, setEntries] = useState<DoctorQueueEntry[]>([]);
  const [filter, setFilter] = useState<QueueFilter>("ALL");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadQueue() {
      try {
        const response = await getDoctorQueue();

        if (!cancelled) {
          setEntries(response.entries);
          setError("");
        }
      } catch (error) {
        if (!cancelled) {
          setError(
            error instanceof Error ? error.message : "Unable to load the queue",
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadQueue();

    const interval = window.setInterval(() => {
      void loadQueue();
    }, 15000);

    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, []);

  const counts = {
    ALL: entries.length,
    WAITING: entries.filter((entry) => entry.status === "WAITING").length,
    PROMOTION_PENDING: entries.filter(
      (entry) => entry.status === "PROMOTION_PENDING",
    ).length,
    CALLED: entries.filter((entry) => entry.status === "CALLED").length,
    IN_CONSULTATION: entries.filter(
      (entry) => entry.status === "IN_CONSULTATION",
    ).length,
  };

  const filteredEntries =
    filter === "ALL"
      ? entries
      : entries.filter((entry) => entry.status === filter);

  function handleOpen(entry: DoctorQueueEntry) {
    navigate(
      `/cases/${entry.session_id}?queueEntryId=${encodeURIComponent(
        entry.queue_entry_id,
      )}`,
    );
  }

  return (
    <main className="min-h-screen bg-background">
      <DoctorHeader user={user} onLogout={logout} showThemeToggle />

      <div className="mx-auto w-full max-w-[1180px] px-7 pb-16 pt-7">
        <div className="mb-1.5 flex flex-wrap items-end justify-between gap-5">
          <div>
            <h1 className="font-display text-[27px] font-medium tracking-[-0.01em] text-primary-dark">
              Your queue
            </h1>

            <p className="mt-1 text-[13.5px] text-text-secondary">
              {filteredEntries.length}{" "}
              {filteredEntries.length === 1 ? "patient" : "patients"} · General
              Medicine
            </p>
          </div>
        </div>

        <div className="my-[22px] flex flex-wrap gap-2">
          {QUEUE_FILTERS.map((option) => {
            const active = filter === option.value;

            return (
              <Button
                className={[
                  "h-auto rounded-full border-[1.5px] px-3.5 py-[7px] text-xs font-bold shadow-none",
                  active
                    ? "border-primary-dark bg-primary-dark text-surface-alt hover:bg-primary-dark"
                    : "border-border bg-surface-alt text-text-secondary hover:border-primary hover:bg-surface-alt hover:text-primary-dark",
                ].join(" ")}
                key={option.value}
                onClick={() => setFilter(option.value)}
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

        {error && (
          <div className="mb-5 rounded-[8px] border border-danger/30 bg-accent-tint px-4 py-3">
            <p className="text-[13px] text-danger">{error}</p>
          </div>
        )}

        {isLoading ? (
          <div className="rounded-[20px] border border-border bg-surface px-5 py-16 text-center">
            <p className="text-[13px] text-text-secondary">Loading queue...</p>
          </div>
        ) : filteredEntries.length === 0 ? (
          <div className="rounded-[20px] border-[1.5px] border-dashed border-border px-5 py-16 text-center">
            <div className="mb-2.5 text-[28px]">🌤️</div>
            <p className="text-[13px] text-text-secondary">
              No patients in this view right now.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-[repeat(auto-fill,minmax(268px,1fr))] gap-4">
            {filteredEntries.map((entry) => (
              <QueueCard
                entry={entry}
                key={entry.queue_entry_id}
                onOpen={handleOpen}
              />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
