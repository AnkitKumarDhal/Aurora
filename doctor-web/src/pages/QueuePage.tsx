import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import DoctorHeader from "@/components/layout/DoctorHeader";
import { useAuth } from "@/auth/useAuth";
import type { DoctorQueueEntry } from "@/types/api";
import QueueCard from "@/features/queue/components/QueueCard";
import QueueEmptyState from "@/features/queue/components/QueueEmptyState";
import QueueFilters, {
  type QueueFilter,
} from "@/features/queue/components/QueueFilters";
import QueueSkeleton from "@/features/queue/components/QueueSkeleton";
import { useDoctorQueue } from "@/features/queue/hooks/useDoctorQueue";

export default function QueuePage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { entries, error, isLoading } = useDoctorQueue();
  const [filter, setFilter] = useState<QueueFilter>("ALL");

  const counts = useMemo(
    () => ({
      ALL: entries.length,
      WAITING: entries.filter((entry) => entry.status === "WAITING").length,
      PROMOTION_PENDING: entries.filter(
        (entry) => entry.status === "PROMOTION_PENDING",
      ).length,
      CALLED: entries.filter((entry) => entry.status === "CALLED").length,
      IN_CONSULTATION: entries.filter(
        (entry) => entry.status === "IN_CONSULTATION",
      ).length,
    }),
    [entries],
  );

  const filteredEntries = useMemo(
    () =>
      filter === "ALL"
        ? entries
        : entries.filter((entry) => entry.status === filter),
    [entries, filter],
  );

  function handleOpen(entry: DoctorQueueEntry): void {
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
        <div className="mb-1.5">
          <h1 className="font-display text-[27px] font-medium tracking-[-0.01em] text-primary-dark">
            Your queue
          </h1>

          <p className="mt-1 text-[13.5px] text-text-secondary">
            {filteredEntries.length}{" "}
            {filteredEntries.length === 1 ? "patient" : "patients"} · General
            Medicine
          </p>
        </div>

        <QueueFilters counts={counts} onChange={setFilter} value={filter} />

        {error && (
          <div className="mb-5 rounded-[8px] border border-danger/30 bg-accent-tint px-4 py-3">
            <p className="text-[13px] text-danger">{error}</p>
          </div>
        )}

        {isLoading ? (
          <QueueSkeleton />
        ) : filteredEntries.length === 0 ? (
          <QueueEmptyState />
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
