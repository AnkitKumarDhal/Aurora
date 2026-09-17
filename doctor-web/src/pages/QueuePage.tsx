import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Activity, LogOut, RefreshCw, UserRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/auth/useAuth";
import { getDoctorQueue } from "@/api/queue";
import type { DoctorQueueEntry, QueueStatus, UrgencyLevel } from "@/types/api";

type QueueFilter = "ALL" | QueueStatus;

const QUEUE_FILTERS: QueueFilter[] = [
  "ALL",
  "WAITING",
  "PROMOTION_PENDING",
  "CALLED",
  "IN_CONSULTATION",
];

function severityClass(level: UrgencyLevel | null): string {
  switch (level) {
    case 1:
      return "border-l-green-500";
    case 2:
      return "border-l-primary";
    case 3:
      return "border-l-yellow-500";
    case 4:
      return "border-l-orange-400";
    case 5:
      return "border-l-red-500";
    default:
      return "border-l-muted";
  }
}

function statusLabel(status: QueueStatus): string {
  switch (status) {
    case "WAITING":
      return "Waiting";
    case "PROMOTION_PENDING":
      return "Promotion pending";
    case "CALLED":
      return "Called";
    case "IN_CONSULTATION":
      return "In consultation";
    case "COMPLETED":
      return "Completed";
    case "CANCELLED":
      return "Cancelled";
    default:
      return status;
  }
}

function urgencyLabel(level: UrgencyLevel | null): string {
  return level === null ? "Unrated" : `Level ${level}`;
}

function formatWaitingTime(seconds: number | null): string {
  if (seconds === null) {
    return "Waiting time unavailable";
  }

  const totalMinutes = Math.floor(seconds / 60);
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;

  if (hours > 0) {
    return `${hours}h ${minutes}m waiting`;
  }

  return `${minutes}m waiting`;
}

function QueueCard({
  entry,
  onOpen,
}: {
  entry: DoctorQueueEntry;
  onOpen: (sessionId: string) => void;
}) {
  const patientName = entry.patient?.display_name ?? "Unknown patient";
  const age = entry.patient?.age;
  const complaint =
    entry.summary?.chief_complaint ?? "No chief complaint available";

  return (
    <button
      className={`group flex min-h-56 flex-col rounded-2xl border border-l-4 bg-card p-5 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-md ${severityClass(entry.urgency_level)}`}
      onClick={() => onOpen(entry.session_id)}
      type="button"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-lg font-semibold tracking-tight">{patientName}</p>
          <p className="mt-1 text-sm text-muted-foreground">
            {age !== null && age !== undefined
              ? `${age} years`
              : "Age unavailable"}
          </p>
        </div>

        <span className="rounded-full border px-2.5 py-1 text-xs font-medium text-muted-foreground">
          {statusLabel(entry.status)}
        </span>
      </div>

      <div className="mt-6">
        <p className="text-sm text-muted-foreground">Chief complaint</p>
        <p className="mt-1 line-clamp-2 text-sm leading-6">{complaint}</p>
      </div>

      <div className="mt-auto flex items-end justify-between gap-4 pt-6">
        <div>
          <p className="text-xs text-muted-foreground">Urgency</p>
          <p className="mt-1 text-sm font-medium">
            {urgencyLabel(entry.urgency_level)}
          </p>
        </div>

        <div className="text-right">
          <p className="text-xs text-muted-foreground">Queue position</p>
          <p className="mt-1 text-sm font-medium">{entry.position ?? "—"}</p>
        </div>
      </div>

      <div className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
        <Activity className="size-4" />
        {formatWaitingTime(entry.waiting_time_seconds)}
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

  return (
    <main className="min-h-screen bg-background">
      <header className="sticky top-0 z-10 border-b bg-background/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Aurora</h1>
            <p className="text-sm text-muted-foreground">General Medicine</p>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden items-center gap-2 rounded-full border px-3 py-2 text-sm md:flex">
              <UserRound className="size-4 text-muted-foreground" />
              <span>{user?.username}</span>
            </div>

            <Button
              onClick={handleRefresh}
              size="icon"
              variant="outline"
              disabled={isRefreshing}
              type="button"
            >
              <RefreshCw
                className={isRefreshing ? "size-4 animate-spin" : "size-4"}
              />
            </Button>

            <Button
              onClick={logout}
              size="icon"
              variant="outline"
              type="button"
            >
              <LogOut className="size-4" />
            </Button>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-6 py-8">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">
              Doctor queue
            </p>
            <h2 className="mt-1 text-3xl font-semibold tracking-tight">
              Your patients
            </h2>
          </div>

          <div className="flex flex-wrap gap-2">
            {QUEUE_FILTERS.map((option) => (
              <Button
                key={option}
                onClick={() => setFilter(option)}
                size="sm"
                variant={filter === option ? "default" : "outline"}
                type="button"
              >
                {option === "ALL" ? "All" : statusLabel(option)}
              </Button>
            ))}
          </div>
        </div>

        {error && (
          <div className="mt-6 rounded-xl border border-destructive/30 bg-destructive/5 p-4">
            <p className="text-sm text-destructive">{error}</p>
          </div>
        )}

        {isLoading ? (
          <div className="mt-8 rounded-2xl border bg-card p-8 text-center">
            <p className="text-sm text-muted-foreground">Loading queue...</p>
          </div>
        ) : filteredEntries.length === 0 ? (
          <div className="mt-8 rounded-2xl border bg-card p-8 text-center">
            <p className="font-medium">No patients in this view</p>
            <p className="mt-1 text-sm text-muted-foreground">
              The queue will refresh automatically.
            </p>
          </div>
        ) : (
          <div className="mt-8 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {filteredEntries.map((entry) => (
              <QueueCard
                key={entry.queue_entry_id}
                entry={entry}
                onOpen={(sessionId) => navigate(`/cases/${sessionId}`)}
              />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
