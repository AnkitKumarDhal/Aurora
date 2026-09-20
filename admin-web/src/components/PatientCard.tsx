import { cn } from "@/lib/utils";
import type { Patient } from "@/types/admin";

interface PatientCardProps {
  patient: Patient;
  selected: boolean;
  onClick: () => void;
}

function formatWait(seconds: number | null): string {
  if (seconds === null) {
    return "—";
  }

  if (seconds < 60) {
    return "<1m";
  }

  const totalMinutes = Math.floor(seconds / 60);
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;

  if (hours > 0) {
    return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`;
  }

  return `${totalMinutes}m`;
}

export function PatientCard({ patient, selected, onClick }: PatientCardProps) {
  const isPriority = patient.urgencyLevel !== null && patient.urgencyLevel >= 4;
  const isPromotionPending = patient.state === "PROMOTION_PENDING";
  const isConsultation = patient.state === "IN_CONSULTATION";
  const isPast = patient.state === "COMPLETED" || patient.state === "CANCELLED";

  return (
    <div
      className={cn(
        "patient-card",
        (isPriority || isPromotionPending) && "priority",
        isConsultation && "consultation",
        isPast && "completed",
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

        <div className="priority-chip">
          {isPriority || isPromotionPending
            ? "HIGH"
            : isPast
              ? "CLOSED"
              : "NORMAL"}
        </div>
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
          {isConsultation
            ? "In session"
            : formatWait(patient.waitingTimeSeconds)}
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
