import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { RefreshCw } from "lucide-react";
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
} {
  switch (level) {
    case 1:
      return {
        border: "border-t-success",
        background: "bg-success/10",
        label: "Level 1 · Routine",
      };
    case 2:
      return {
        border: "border-t-primary",
        background: "bg-primary/10",
        label: "Level 2 · Low",
      };
    case 3:
      return {
        border: "border-t-warning",
        background: "bg-warning/10",
        label: "Level 3 · Moderate",
      };
    case 4:
      return {
        border: "border-t-accent",
        background: "bg-accent/15",
        label: "Level 4 · Elevated",
      };
    case 5:
      return {
        border: "border-t-danger",
        background: "bg-danger/10",
        label: "Level 5 · Critical",
      };
    default:
      return {
        border: "border-t-border",
        background: "bg-muted",
        label: "Unrated",
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
        text: "text-text-primary",
        label: "Waiting",
      };
    case "PROMOTION_PENDING":
      return {
        background: "bg-accent-tint",
        text: "text-accent-dark",
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
        text: "text-text-primary",
        label: "Completed",
      };
    case "CANCELLED":
      return {
        background: "bg-muted",
        text: "text-text-secondary",
        label: "Cancelled",
      };
    default:
      return {
        background: "bg-muted",
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
      className={`group flex min-h-[140px] flex-col rounded-xl border border-border border-t-4 bg-surface p-4 text-left shadow-[0_8px_24px_rgba(58,46,92,0.05)] transition duration-200 hover:-translate-y-0.5 hover:shadow-[0_12px_30px_rgba(58,46,92,0.08)] ${severity.border}`}
      onClick={() => onOpen(entry)}
      type="button"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate font-display text-[15px] font-semibold text-text-primary">
            {entry.patient?.display_name ?? "Unknown patient"}
          </p>

          <p className="mt-0.5 text-[10px] font-medium text-text-secondary">
            {entry.patient?.age !== null && entry.patient?.age !== undefined
              ? `${entry.patient.age} yrs`
              : "Age unavailable"}{" "}
            · position {entry.position ?? "—"}
          </p>
        </div>

        <span
          className={`shrink-0 rounded-full px-2 py-1 text-[9px] font-semibold ${severity.background} text-text-primary`}
        >
          {severity.label}
        </span>
      </div>

      <p className="mt-3 line-clamp-2 text-[11px] leading-4 text-text-primary">
        {entry.summary?.chief_complaint ?? "No chief complaint available"}
      </p>

      <div className="mt-auto flex items-center justify-between pt-3">
        <span
          className={`rounded-full px-2.5 py-1 text-[9px] font-semibold ${status.background} ${status.text}`}
        >
          <span className="mr-1 inline-block size-1.5 rounded-full bg-current align-middle" />
          {status.label}
        </span>

        <span className="text-[10px] font-medium text-text-secondary">
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
  const [isRefreshing, setIsRefreshing] = useState(false);
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
          setIsRefreshing(false);
        }
      }
    }

    void loadQueue();

    const interval = window.setInterval(() => {
      setIsRefreshing(true);
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

  async function handleRefresh() {
    setIsRefreshing(true);

    try {
      const response = await getDoctorQueue();
      setEntries(response.entries);
      setError("");
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "Unable to refresh the queue",
      );
    } finally {
      setIsRefreshing(false);
    }
  }

  function handleOpen(entry: DoctorQueueEntry) {
    navigate(
      `/cases/${entry.session_id}?queueEntryId=${encodeURIComponent(
        entry.queue_entry_id,
      )}`,
    );
  }

  return (
    <main className="min-h-screen bg-background">
      <DoctorHeader user={user} onLogout={logout} />

      <div className="mx-auto max-w-[950px] px-5 pb-12 pt-7">
        <div className="flex flex-col gap-4">
          <div>
            <h1 className="font-display text-[29px] font-semibold tracking-[-0.02em] text-text-primary">
              Your queue
            </h1>

            <p className="mt-1 text-[11px] font-medium text-text-secondary">
              {entries.length} patients · General Medicine
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            {QUEUE_FILTERS.map((option) => {
              const active = filter === option.value;

              return (
                <Button
                  className={[
                    "h-7 rounded-full border px-3 text-[10px] font-semibold shadow-none",
                    active
                      ? "border-primary-dark bg-primary-dark text-white hover:bg-primary-dark/90"
                      : "border-border bg-surface text-text-secondary hover:bg-primary-tint hover:text-text-primary",
                  ].join(" ")}
                  key={option.value}
                  onClick={() => setFilter(option.value)}
                  type="button"
                  variant="outline"
                >
                  {option.label}
                  <span
                    className={[
                      "ml-1.5 rounded-full px-1.5 py-0.5 text-[8px]",
                      active
                        ? "bg-white/15 text-white"
                        : "bg-primary-tint text-text-secondary",
                    ].join(" ")}
                  >
                    {counts[option.value]}
                  </span>
                </Button>
              );
            })}

            <Button
              aria-label="Refresh queue"
              className="ml-auto size-7 rounded-full border-border bg-surface text-text-secondary hover:bg-primary-tint hover:text-text-primary"
              disabled={isRefreshing}
              onClick={handleRefresh}
              size="icon"
              type="button"
              variant="outline"
            >
              <RefreshCw
                className={isRefreshing ? "size-3.5 animate-spin" : "size-3.5"}
              />
            </Button>
          </div>
        </div>

        {error && (
          <div className="mt-5 rounded-xl border border-danger/25 bg-accent-tint px-4 py-3">
            <p className="text-[11px] text-accent-dark">{error}</p>
          </div>
        )}

        {isLoading ? (
          <div className="mt-5 rounded-xl border border-border bg-surface px-5 py-10 text-center shadow-[0_8px_24px_rgba(58,46,92,0.04)]">
            <p className="text-[11px] text-text-secondary">Loading queue...</p>
          </div>
        ) : filteredEntries.length === 0 ? (
          <div className="mt-5 rounded-xl border border-border bg-surface px-5 py-10 text-center shadow-[0_8px_24px_rgba(58,46,92,0.04)]">
            <p className="font-display text-[16px] font-semibold text-text-primary">
              No patients in this view
            </p>
            <p className="mt-1 text-[10px] text-text-secondary">
              The queue will refresh automatically.
            </p>
          </div>
        ) : (
          <div className="mt-5 grid grid-cols-1 gap-3.5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
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
