import { cn } from "@/lib/utils";
import { initialDoctors } from "@/data/mockData";
import { useAdminStore } from "@/store/adminStore";

export function DoctorsPanel() {
  const selectedDoctorFilter = useAdminStore(
    (state) => state.selectedDoctorFilter,
  );
  const setDoctorFilter = useAdminStore((state) => state.setDoctorFilter);

  return (
    <div className="panel">
      <div className="panel-title">Doctors</div>

      <div className="doctor-list">
        {initialDoctors.map((doctor) => {
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
                  doctor.status === "Consulting" && "consulting",
                  doctor.status === "Unavailable" && "unavailable",
                )}
              />
              <div className="doctor-name">{doctor.name}</div>
              <div
                className={cn(
                  "doctor-status",
                  doctor.status === "Consulting" && "consulting",
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
