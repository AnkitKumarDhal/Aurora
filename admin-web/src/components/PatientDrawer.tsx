import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { initialDoctors } from "@/data/mockData";
import { useAdminStore } from "@/store/adminStore";
import type { Patient } from "@/types/admin";

export function PatientDrawer() {
  const selectedPatientId = useAdminStore((state) => state.selectedPatientId);
  const isDrawerOpen = useAdminStore((state) => state.isDrawerOpen);
  const isReassigning = useAdminStore((state) => state.isReassigning);
  const patients = useAdminStore((state) => state.patients);
  const closeDrawer = useAdminStore((state) => state.closeDrawer);
  const openReassign = useAdminStore((state) => state.openReassign);
  const cancelReassign = useAdminStore((state) => state.cancelReassign);
  const confirmReassign = useAdminStore((state) => state.confirmReassign);

  const patient = patients.find((item) => item.id === selectedPatientId);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && isDrawerOpen) {
        closeDrawer();
      }
    };

    document.addEventListener("keydown", handleKeyDown);

    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [closeDrawer, isDrawerOpen]);

  if (!patient) {
    return null;
  }

  return (
    <>
      <div
        className={cn("drawer-overlay", isDrawerOpen && "open")}
        onClick={closeDrawer}
      />

      <aside
        className={cn("drawer", isDrawerOpen && "open")}
        aria-hidden={!isDrawerOpen}
      >
        <div className="drawer-header">
          <div>
            <div className="drawer-patient-id">{patient.id}</div>
            <div
              style={{
                fontFamily: "'JetBrains Mono',monospace",
                fontSize: "11px",
                color: "var(--color-text-secondary)",
                marginTop: "4px",
              }}
            >
              {patient.name} · {patient.ageSex} · {patient.mrn}
            </div>
          </div>

          <button
            className="drawer-close"
            type="button"
            onClick={closeDrawer}
            aria-label="Close patient drawer"
          >
            ✕
          </button>
        </div>

        <div
          className={cn(
            "drawer-body",
            "detail-view",
            isReassigning && "hidden",
          )}
        >
          <DetailView patient={patient} />
        </div>

        <ReassignPanel
          patient={patient}
          active={isReassigning}
          onCancel={cancelReassign}
          onConfirm={confirmReassign}
        />

        <div
          className="drawer-actions"
          style={{
            display: isReassigning ? "none" : "flex",
          }}
        >
          <button className="btn" type="button" onClick={closeDrawer}>
            Close
          </button>
          <button
            className="btn btn-primary"
            type="button"
            onClick={openReassign}
          >
            Reassign
          </button>
        </div>
      </aside>
    </>
  );
}

function DetailView({ patient }: { patient: Patient }) {
  return (
    <>
      <div>
        <div className="drawer-section-title">Status</div>

        <div
          style={{
            display: "flex",
            gap: "6px",
            flexWrap: "wrap",
            marginBottom: "8px",
          }}
        >
          <span
            className={cn(
              "drawer-status-badge",
              patient.priority === "High Priority" && "priority",
            )}
          >
            {patient.priority}
          </span>
          <span
            className={cn(
              "drawer-status-badge",
              patient.state === "In Consultation" && "consultation",
            )}
          >
            {patient.state}
          </span>
        </div>
      </div>

      <div>
        <div className="drawer-section-title">Details</div>

        <div className="drawer-row">
          <div className="drawer-field">
            <div className="drawer-field-label">Wait Time</div>
            <div className="drawer-field-value">{patient.wait}</div>
          </div>

          <div className="drawer-field">
            <div className="drawer-field-label">Assigned</div>
            <div className="drawer-field-value">{patient.doctor}</div>
          </div>

          <div className="drawer-field">
            <div className="drawer-field-label">Severity</div>
            <div className="drawer-field-value">High</div>
          </div>

          <div className="drawer-field">
            <div className="drawer-field-label">Triage</div>
            <div className="drawer-field-value">ESI-2</div>
          </div>
        </div>
      </div>

      <div>
        <div className="drawer-section-title">Chief Complaint</div>

        <div
          style={{
            fontSize: "13px",
            color: "var(--color-text-primary)",
            lineHeight: "1.5",
          }}
        >
          {patient.complaint}
        </div>
      </div>

      <div>
        <div className="drawer-section-title">Timeline</div>

        <div className="timeline">
          <div className="timeline-item">
            <div>Entered queue</div>
            <div className="timeline-time">14:22</div>
          </div>

          <div className="timeline-item">
            <div>Triage completed — High priority</div>
            <div className="timeline-time">14:24</div>
          </div>

          <div className="timeline-item current">
            <div>
              {patient.doctor === "Unassigned"
                ? "Awaiting doctor assignment"
                : `Assigned to ${patient.doctor}`}
            </div>
            <div className="timeline-time">14:31</div>
          </div>
        </div>
      </div>
    </>
  );
}

function ReassignPanel({
  patient,
  active,
  onCancel,
  onConfirm,
}: {
  patient: Patient;
  active: boolean;
  onCancel: () => void;
  onConfirm: (doctorName: string) => void;
}) {
  const [chosenDoctor, setChosenDoctor] = useState("");

  if (!active) {
    return null;
  }

  const currentDoctor =
    patient.doctor === "Unassigned" ? "" : patient.doctor.replace("Dr. ", "");

  return (
    <div className="drawer-body reassign-panel active">
      <div>
        <div className="drawer-section-title">Reassign Patient</div>

        <div className="reassign-info">
          <div className="reassign-info-label">Current Doctor</div>
          <div className="reassign-info-value">{patient.doctor}</div>
        </div>
      </div>

      <div className="reassign-select-wrap">
        <label htmlFor="reassignDoctor">Reassign to</label>

        <select
          className="reassign-select"
          id="reassignDoctor"
          value={chosenDoctor}
          onChange={(event) => setChosenDoctor(event.target.value)}
        >
          <option value="">Select a doctor…</option>

          {initialDoctors.map((doctor) => {
            const isCurrent = doctor.id === currentDoctor;
            const disabled = doctor.status === "Unavailable" || isCurrent;

            return (
              <option key={doctor.id} value={doctor.id} disabled={disabled}>
                {doctor.name} · {isCurrent ? "(current)" : doctor.status} ·{" "}
                {doctor.assignedCount} assigned
              </option>
            );
          })}
        </select>
      </div>

      <div className="reassign-note">
        The patient will be moved to the selected doctor's queue. Current
        consultation state (if any) will be preserved.
      </div>

      <div className="reassign-actions">
        <button className="btn btn-cancel" type="button" onClick={onCancel}>
          Cancel
        </button>

        <button
          className="btn btn-confirm"
          type="button"
          onClick={() => {
            if (chosenDoctor) {
              onConfirm(`Dr. ${chosenDoctor}`);
            }
          }}
          disabled={!chosenDoctor}
        >
          Confirm
        </button>
      </div>
    </div>
  );
}
