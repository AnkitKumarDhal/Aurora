import { cn } from "@/lib/utils";
import type { Patient } from "@/types/admin";

interface PatientCardProps {
  patient: Patient;
  selected: boolean;
  onClick: () => void;
}

function formatWait(patient: Patient): string {
  if (patient.state === "IN_CONSULTATION") {
    return "In session";
  }

  if (patient.waitingTimeSeconds === null) {
    return "—";
  }

  return `${Math.floor(patient.waitingTimeSeconds / 60)} min`;
}

export function PatientCard({ patient, selected, onClick }: PatientCardProps) {
  const isPriority = patient.urgencyLevel !== null && patient.urgencyLevel >= 4;

  const isConsultation = patient.state === "IN_CONSULTATION";

  return (
    <div
      className={cn(
        "patient-card",
        isPriority && "priority",
        isConsultation && "consultation",
        selected && "selected",
      )}
      data-id={patient.id}
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onClick();
        }
      }}
    >
      <div className="card-top">
        <div className="patient-id">{patient.id}</div>

        <div className="priority-chip">{isPriority ? "HIGH" : "NORMAL"}</div>
      </div>

      <div className="card-name">
        {patient.name}
        {patient.age !== null && ` · ${patient.age}`}
      </div>

      <div className="card-complaint">
        {patient.complaint ?? "No complaint recorded"}
      </div>

      <div className="card-meta">
        <div className={cn("card-wait", isConsultation && "card-wait-session")}>
          {formatWait(patient)}
        </div>

        <div className="card-triage">
          {patient.urgencyLevel !== null
            ? `Level ${patient.urgencyLevel}`
            : "Level —"}
        </div>
      </div>

      {patient.doctor ? (
        <div className="card-assign">
          <span className="arrow">→</span> {patient.doctor}
        </div>
      ) : (
        <div className="card-assign unassigned">⚠ Unassigned</div>
      )}
    </div>
  );
}
