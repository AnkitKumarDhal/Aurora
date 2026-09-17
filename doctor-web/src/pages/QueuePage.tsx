import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import DoctorHeader from "@/components/layout/DoctorHeader";
import { useAuth } from "@/auth/useAuth";
import { getDoctorQueue } from "@/api/queue";
import type { DoctorQueueEntry, QueueStatus, UrgencyLevel } from "@/types/api";

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

function severityMeta(level: UrgencyLevel | null): {
  border: string;
  background: string;
  label: string;
  text: string;
} {
  switch (level) {
    case 1:
      return {
        border: "border-t-success",
        background: "bg-success/10",
        label: "Level 1 · Routine",
        text: "text-text-primary",
      };
    case 2:
      return {
        border: "border-t-primary",
        background: "bg-primary-tint",
        label: "Level 2 · Low",
        text: "text-primary-dark",
      };
    case 3:
      return {
        border: "border-t-warning",
        background: "bg-warning/15",
        label: "Level 3 · Moderate",
        text: "text-text-primary",
      };
    case 4:
      return {
        border: "border-t-accent",
        background: "bg-accent-tint",
        label: "Level 4 · Elevated",
        text: "text-accent-dark",
      };
    case 5:
      return {
        border: "border-t-danger",
        background: "bg-danger/10",
        label: "Level 5 · Critical",
        text: "text-danger",
      };
    default:
      return {
        border: "border-t-border",
        background: "bg-primary-tint",
        label: "Unrated",
        text: "text-text-primary",
      };
  }
}

function statusMeta(status: QueueStatus): {
  background: string;
  text: string;
  label: string;
} {
  switch (status) {
    case "WAITING":
      return {
        background: "bg-primary-tint",
        text: "text-primary-dark",
        label: "Waiting",
      };
    case "PROMOTION_PENDING":
      return {
        background: "bg-warning/20",
        text: "text-text-primary",
        label: "Promotion review",
      };
    case "CALLED":
      return {
        background: "bg-accent-tint",
        text: "text-accent-dark",
        label: "Called",
      };
    case "IN_CONSULTATION":
      return {
        background: "bg-success/15",
        text: "text-text-primary",
        label: "In consultation",
      };
    case "COMPLETED":
      return {
        background: "bg-primary-tint",
        text: "text-text-secondary",
        label: "Completed",
      };
    case "CANCELLED":
      return {
        background: "bg-primary-tint",
        text: "text-text-secondary",
        label: "Cancelled",
      };
    default:
      return {
        background: "bg-primary-tint",
        text: "text-text-secondary",
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
  const severity = severityMeta(entry.urgency_level);
  const status = statusMeta(entry.status);

  return (
    <button
      className={`group flex min-h-[140px] flex-col overflow-hidden rounded-[14px] border border-border bg-surface p-[18px] pb-4 text-left shadow-[0_10px_24px_-18px_rgba(58,46,92,0.4)] transition duration-150 hover:-translate-y-[3px] hover:border-primary hover:shadow-[0_20px_32px_-18px_rgba(58,46,92,0.45)] ${severity.border}`}
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
          className={`shrink-0 rounded-full px-[9px] py-[3px] text-[10.5px] font-extrabold ${severity.background} ${severity.text}`}
        >
          {severity.label}
        </span>
      </div>

      <p className="mb-3.5 mt-1 min-h-[2.6em] line-clamp-2 text-[13px] leading-[1.5] text-text-primary">
        {entry.summary?.chief_complaint ?? "No chief complaint available"}
      </p>

      <div className="mt-auto flex items-center justify-between">
        <span
          className={`inline-flex items-center gap-[5px] rounded-full px-2.5 py-1 text-[11px] font-bold ${status.background} ${status.text}`}
        >
          <span className="size-1.5 rounded-full bg-current" />
          {status.label}
        </span>

        <span className="text-xs tabular-nums text-text-secondary">
          {formatWaitingTime(entry.waiting_time_seconds)}
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
