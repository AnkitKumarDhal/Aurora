import type { QueueStatus } from "@/types/api";

export interface QueueStatusStyles {
  background: string;
  text: string;
  dot: string;
  label: string;
}

export function getQueueStatusStyles(status: QueueStatus): QueueStatusStyles {
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
  }
}

export function formatWaitingTime(seconds: number | null): string {
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
