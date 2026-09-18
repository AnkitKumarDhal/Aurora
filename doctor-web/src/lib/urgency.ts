import type { UrgencyLevel } from "@/types/api";

export interface UrgencyStyles {
  accent: string;
  badgeBackground: string;
  badgeColor: string;
  label: string;
}

export function getUrgencyStyles(level: UrgencyLevel | null): UrgencyStyles {
  switch (level) {
    case 1:
      return {
        accent: "before:bg-success",
        badgeBackground:
          "color-mix(in srgb, var(--aurora-success) 16%, var(--aurora-surface))",
        badgeColor:
          "color-mix(in srgb, var(--aurora-success) 55%, var(--aurora-text-primary))",
        label: "Routine",
      };
    case 2:
      return {
        accent: "before:bg-primary",
        badgeBackground: "var(--aurora-primary-tint)",
        badgeColor: "var(--aurora-primary-dark)",
        label: "Low",
      };
    case 3:
      return {
        accent: "before:bg-warning",
        badgeBackground:
          "color-mix(in srgb, var(--aurora-warning) 20%, var(--aurora-surface))",
        badgeColor:
          "color-mix(in srgb, var(--aurora-warning) 60%, var(--aurora-text-primary))",
        label: "Moderate",
      };
    case 4:
      return {
        accent: "before:bg-accent",
        badgeBackground: "var(--aurora-accent-tint)",
        badgeColor: "var(--aurora-accent-dark)",
        label: "Elevated",
      };
    case 5:
      return {
        accent: "before:bg-danger",
        badgeBackground:
          "color-mix(in srgb, var(--aurora-danger) 18%, var(--aurora-surface))",
        badgeColor: "var(--aurora-danger)",
        label: "Critical",
      };
    default:
      return {
        accent: "before:bg-border",
        badgeBackground: "var(--aurora-primary-tint)",
        badgeColor: "var(--aurora-text-secondary)",
        label: "Unrated",
      };
  }
}
