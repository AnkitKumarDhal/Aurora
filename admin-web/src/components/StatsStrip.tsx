import type { DashboardStats } from "@/types/admin";

interface StatsStripProps {
  stats: DashboardStats;
}

export function StatsStrip({ stats }: StatsStripProps) {
  const items = [
    {
      value: stats.patients,
      label: "Patients Today",
    },
    {
      value: stats.waiting,
      label: "Waiting",
    },
    {
      value: stats.in_consultation,
      label: "In Consultation",
    },
    {
      value: stats.doctors,
      label: "Doctors",
    },
  ];

  return (
    <div className="stats">
      {items.map((stat) => (
        <div className="stat" key={stat.label}>
          <div className="stat-value">{stat.value}</div>

          <div className="stat-label">{stat.label}</div>
        </div>
      ))}
    </div>
  );
}
