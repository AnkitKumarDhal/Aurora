import { cn } from "@/lib/utils";
import { PatientCard } from "@/components/PatientCard";
import { useAdminStore } from "@/store/adminStore";
import type { Patient } from "@/types/admin";

interface PatientBoardProps {
  patients: Patient[];
}

function isPriority(patient: Patient): boolean {
  return (
    patient.state === "PROMOTION_PENDING" ||
    (patient.urgencyLevel !== null &&
      patient.urgencyLevel >= 4 &&
      patient.state !== "COMPLETED" &&
      patient.state !== "CANCELLED")
  );
}

function isPast(patient: Patient): boolean {
  return patient.state === "COMPLETED" || patient.state === "CANCELLED";
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
  variant?: "priority" | "consultation" | "past";
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

  const consultationPatients = filteredPatients.filter(
    (patient) => patient.state === "IN_CONSULTATION",
  );

  const pastPatients = filteredPatients.filter(isPast);

  const waitingPatients = filteredPatients.filter(
    (patient) =>
      !isPriority(patient) &&
      !isPast(patient) &&
      patient.state !== "IN_CONSULTATION",
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

          <div className="flow-dot" />

          <span>History</span>
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

      <Lane
        title="Past Today"
        count={pastPatients.length}
        patients={pastPatients}
        variant="past"
      />
    </section>
  );
}
