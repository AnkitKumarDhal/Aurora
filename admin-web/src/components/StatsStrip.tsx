const stats = [
  { value: "24", label: "Patients" },
  { value: "6", label: "Waiting" },
  { value: "4", label: "In Consultation" },
  { value: "5", label: "Doctors" },
];

export function StatsStrip() {
  return (
    <div className="stats">
      {stats.map((stat) => (
        <div className="stat" key={stat.label}>
          <div className="stat-value">{stat.value}</div>
          <div className="stat-label">{stat.label}</div>
        </div>
      ))}
    </div>
  );
}
