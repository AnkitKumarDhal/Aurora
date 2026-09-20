import { cn } from "@/lib/utils";
import { useAdminStore } from "@/store/adminStore";
import type { DashboardDoctor } from "@/types/admin";

interface DoctorsPanelProps {
  doctors: DashboardDoctor[];
}

export function DoctorsPanel({ doctors }: DoctorsPanelProps) {
  const selectedDoctorFilter = useAdminStore(
    (state) => state.selectedDoctorFilter,
  );

  const setDoctorFilter = useAdminStore((state) => state.setDoctorFilter);

  return (
    <div className="panel">
      <div className="panel-title">Doctors</div>

      <div className="doctor-list">
        {doctors.map((doctor) => {
          const active = selectedDoctorFilter === doctor.id;

          return (
            <div
              key={doctor.id}
              className={cn("doctor-row", active && "active-filter")}
              role="button"
              tabIndex={0}
              onClick={() => setDoctorFilter(doctor.id)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();

                  setDoctorFilter(doctor.id);
                }
              }}
            >
              <div
                className={cn(
                  "doctor-dot",
                  doctor.status === "Available" && "available",
                  doctor.status === "Unavailable" && "unavailable",
                )}
              />

              <div className="doctor-name">{doctor.name}</div>

              <div
                className={cn(
                  "doctor-status",
                  doctor.status === "Unavailable" && "unavailable",
                )}
              >
                {doctor.status}
              </div>

              <div className="doctor-count">{doctor.assignedCount}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
