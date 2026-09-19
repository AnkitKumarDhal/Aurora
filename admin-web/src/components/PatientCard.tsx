import { cn } from "@/lib/utils";
import type { Patient } from "@/types/admin";

interface PatientCardProps {
  patient: Patient;
  selected: boolean;
  onClick: () => void;
}

export function PatientCard({ patient, selected, onClick }: PatientCardProps) {
  const isPriority = patient.priority === "High Priority";
  const isConsultation = patient.state === "In Consultation";

  return (
    <div
      className={cn(
        "patient-card",
        isPriority && "priority",
        isConsultation && "consultation",
        patient.stale && "stale",
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
        {patient.name} · {patient.ageSex}
      </div>

      <div className="card-complaint">{patient.cardComplaint}</div>

      <div className="card-meta">
        <div className={cn("card-wait", isConsultation && "card-wait-session")}>
          {patient.wait}
          {patient.waitMinutes !== null && <span>min</span>}
        </div>
        <div className="card-triage">{patient.triage}</div>
      </div>

      {patient.doctor === "Unassigned" ? (
        <div className="card-assign unassigned">⚠ Unassigned</div>
      ) : (
        <div className="card-assign">
          <span className="arrow">→</span> {patient.doctor}
        </div>
      )}
    </div>
  );
}
