import { cn } from "@/lib/utils";
import { PatientCard } from "@/components/PatientCard";
import { useAdminStore } from "@/store/adminStore";
import type { Patient } from "@/types/admin";

interface PatientBoardProps {
  patients: Patient[];
}

function isPriority(patient: Patient): boolean {
  return patient.urgencyLevel !== null && patient.urgencyLevel >= 4;
}

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
            key={patient.queueEntryId}
            patient={patient}
            selected={isDrawerOpen && selectedPatientId === patient.id}
            onClick={() => openPatient(patient.id)}
          />
        ))}
      </div>
    </div>
  );
}

export function PatientBoard({ patients }: PatientBoardProps) {
  const selectedDoctorFilter = useAdminStore(
    (state) => state.selectedDoctorFilter,
  );

  const filteredPatients = selectedDoctorFilter
    ? patients.filter((patient) => patient.doctorId === selectedDoctorFilter)
    : patients;

  const priorityPatients = filteredPatients.filter(isPriority);

  const waitingPatients = filteredPatients.filter(
    (patient) => patient.state !== "IN_CONSULTATION" && !isPriority(patient),
  );

  const consultationPatients = filteredPatients.filter(
    (patient) => patient.state === "IN_CONSULTATION",
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
