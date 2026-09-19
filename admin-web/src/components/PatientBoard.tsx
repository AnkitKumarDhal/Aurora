import { cn } from "@/lib/utils";
import { PatientCard } from "@/components/PatientCard";
import { useAdminStore } from "@/store/adminStore";
import type { Patient } from "@/types/admin";

function Lane({
  title,
  count,
  patients,
  variant,
}: {
  title: string;
  count: number;
  patients: Patient[];
  variant?: "priority" | "consultation";
}) {
  const openPatient = useAdminStore((state) => state.openPatient);
  const selectedPatientId = useAdminStore((state) => state.selectedPatientId);
  const isDrawerOpen = useAdminStore((state) => state.isDrawerOpen);

  return (
    <div className={cn("lane", variant)}>
      <div className="lane-header">
        <div className="lane-title">{title}</div>
        <div className="lane-count">{count}</div>
      </div>

      <div className="lane-cards">
        {patients.map((patient) => (
          <PatientCard
            key={patient.id}
            patient={patient}
            selected={isDrawerOpen && selectedPatientId === patient.id}
            onClick={() => openPatient(patient.id)}
          />
        ))}
      </div>
    </div>
  );
}

export function PatientBoard() {
  const patients = useAdminStore((state) => state.patients);

  const priorityPatients = patients.filter(
    (patient) => patient.priority === "High Priority",
  );

  const waitingPatients = patients.filter(
    (patient) => patient.state === "Waiting" && patient.priority === "Normal",
  );

  const consultationPatients = patients.filter(
    (patient) => patient.state === "In Consultation",
  );

  return (
    <section className="board">
      <div className="board-header">
        <div className="board-title">Patient Flow</div>
        <div className="board-flow">
          <span>Queue</span>
          <div className="flow-dot" />
          <span>Assign</span>
          <div className="flow-dot" />
          <span>Consult</span>
        </div>
      </div>

      <Lane
        title="Priority"
        count={priorityPatients.length}
        patients={priorityPatients}
        variant="priority"
      />

      <Lane
        title="Waiting"
        count={waitingPatients.length}
        patients={waitingPatients}
      />

      <Lane
        title="In Consultation"
        count={consultationPatients.length}
        patients={consultationPatients}
        variant="consultation"
      />
    </section>
  );
}
