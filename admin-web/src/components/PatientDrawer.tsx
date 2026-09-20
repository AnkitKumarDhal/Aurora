import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { reassignPatient } from "@/api/admin";
import { useAdminStore } from "@/store/adminStore";
import type { DashboardDoctor, Patient } from "@/types/admin";

interface PatientDrawerProps {
  patients: Patient[];
  doctors: DashboardDoctor[];
  onReassigned: () => Promise<void>;
}

function formatTime(value: string | null): string {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return date.toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
  });
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

function canReassign(patient: Patient): boolean {
  return (
    patient.state === "WAITING" ||
    patient.state === "READY" ||
    patient.state === "CALLED" ||
    patient.state === "PROMOTION_PENDING"
  );
}

export function PatientDrawer({
  patients,
  doctors,
  onReassigned,
}: PatientDrawerProps) {
  const selectedPatientId = useAdminStore((state) => state.selectedPatientId);

  const isDrawerOpen = useAdminStore((state) => state.isDrawerOpen);

  const closeDrawer = useAdminStore((state) => state.closeDrawer);

  const showToast = useAdminStore((state) => state.showToast);

  const [isPresented, setIsPresented] = useState(false);

  const [isReassigning, setIsReassigning] = useState(false);

  const [selectedDoctorId, setSelectedDoctorId] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);

  const [reassignError, setReassignError] = useState<string | null>(null);

  const patient = patients.find((item) => item.id === selectedPatientId);

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      setIsPresented(isDrawerOpen);
    });

    return () => {
      window.cancelAnimationFrame(frame);
    };
  }, [isDrawerOpen]);

  useEffect(() => {
    setIsReassigning(false);
    setSelectedDoctorId("");
    setReassignError(null);
    setIsSubmitting(false);
  }, [selectedPatientId]);

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

  const isPriority =
    patient.urgencyLevel !== null &&
    patient.urgencyLevel >= 4 &&
    patient.state !== "COMPLETED" &&
    patient.state !== "CANCELLED";

  const isPast = patient.state === "COMPLETED" || patient.state === "CANCELLED";

  async function handleConfirmReassign(): Promise<void> {
    if (!selectedDoctorId || isSubmitting) {
      return;
    }

    setIsSubmitting(true);
    setReassignError(null);

    try {
      const result = await reassignPatient(
        patient.queueEntryId,
        selectedDoctorId,
      );

      const targetDoctor = doctors.find(
        (doctor) => doctor.id === result.doctor_id,
      );

      showToast(
        `Reassigned ${patient.name} to ${
          targetDoctor?.name ?? result.doctor_id
        }`,
        "success",
      );

      setIsReassigning(false);
      setSelectedDoctorId("");
      closeDrawer();

      await onReassigned();
    } catch (error) {
      setReassignError(
        error instanceof Error ? error.message : "Unable to reassign patient.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <>
      <div
        className={cn("drawer-overlay", isPresented && "open")}
        onClick={closeDrawer}
      />

      <aside
        className={cn("drawer", isPresented && "open")}
        aria-hidden={!isDrawerOpen}
      >
        <div className="drawer-header">
          <div>
            <div className="drawer-patient-id">{patient.id}</div>

            <div
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: "11px",
                color: "var(--color-text-secondary)",
                marginTop: "4px",
              }}
            >
              {patient.name}

              {patient.age !== null && ` · ${patient.age}`}
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

        {!isReassigning && (
          <div className="drawer-body detail-view">
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
                    isPriority && "priority",
                    isPast && "closed",
                  )}
                >
                  {isPast
                    ? "Past Today"
                    : isPriority
                      ? "High Priority"
                      : "Normal"}
                </span>

                <span className="drawer-status-badge">
                  {patient.state.replaceAll("_", " ")}
                </span>
              </div>
            </div>

            <div>
              <div className="drawer-section-title">Details</div>

              <div className="drawer-row">
                <div className="drawer-field">
                  <div className="drawer-field-label">Wait Time</div>

                  <div className="drawer-field-value">
                    {patient.state === "IN_CONSULTATION"
                      ? "In session"
                      : formatWait(patient.waitingTimeSeconds)}
                  </div>
                </div>

                <div className="drawer-field">
                  <div className="drawer-field-label">Assigned</div>

                  <div className="drawer-field-value">
                    {patient.doctor ?? "Unassigned"}
                  </div>
                </div>

                <div className="drawer-field">
                  <div className="drawer-field-label">Urgency</div>

                  <div className="drawer-field-value">
                    {patient.urgencyLevel !== null
                      ? `Level ${patient.urgencyLevel}`
                      : "—"}
                  </div>
                </div>

                <div className="drawer-field">
                  <div className="drawer-field-label">Priority Score</div>

                  <div className="drawer-field-value">
                    {patient.priorityScore ?? "—"}
                  </div>
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
                {patient.complaint ?? "No complaint recorded."}
              </div>
            </div>

            <div>
              <div className="drawer-section-title">Timeline</div>

              <div className="timeline">
                <div className="timeline-item">
                  <div>Entered queue</div>

                  <div className="timeline-time">
                    {formatTime(patient.queuedAt)}
                  </div>
                </div>

                <div className="timeline-item">
                  <div>
                    {patient.doctor
                      ? `Assigned to ${patient.doctor}`
                      : "Awaiting doctor assignment"}
                  </div>
                </div>

                <div className="timeline-item current">
                  <div>Current state: {patient.state.replaceAll("_", " ")}</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {isReassigning && (
          <div className="drawer-body reassign-panel active">
            <div>
              <div className="drawer-section-title">Reassign Patient</div>

              <div className="reassign-info">
                <div className="reassign-info-label">Current Doctor</div>

                <div className="reassign-info-value">
                  {patient.doctor ?? "Unassigned"}
                </div>
              </div>
            </div>

            <div className="reassign-select-wrap">
              <label htmlFor="reassignDoctor">Reassign to</label>

              <select
                className="reassign-select"
                id="reassignDoctor"
                value={selectedDoctorId}
                disabled={isSubmitting}
                onChange={(event) => {
                  setSelectedDoctorId(event.target.value);
                  setReassignError(null);
                }}
              >
                <option value="">Select a doctor…</option>

                {doctors.map((doctor) => {
                  const isCurrent = doctor.id === patient.doctorId;

                  const disabled = isCurrent || doctor.status === "Unavailable";

                  return (
                    <option
                      key={doctor.id}
                      value={doctor.id}
                      disabled={disabled}
                    >
                      {doctor.name}
                      {" · "}
                      {isCurrent ? "(current)" : doctor.status}
                      {" · "}
                      {doctor.assignedCount} assigned
                    </option>
                  );
                })}
              </select>
            </div>

            <div className="reassign-note">
              The patient will be moved to the selected doctor's queue. The
              current clinical session state is preserved.
            </div>

            {reassignError && (
              <div className="login-error">{reassignError}</div>
            )}

            <div className="reassign-actions">
              <button
                className="btn btn-cancel"
                type="button"
                disabled={isSubmitting}
                onClick={() => {
                  setIsReassigning(false);
                  setSelectedDoctorId("");
                  setReassignError(null);
                }}
              >
                Cancel
              </button>

              <button
                className="btn btn-confirm"
                type="button"
                disabled={!selectedDoctorId || isSubmitting}
                onClick={() => void handleConfirmReassign()}
              >
                {isSubmitting ? "Saving..." : "Confirm"}
              </button>
            </div>
          </div>
        )}

        {!isReassigning && (
          <div className="drawer-actions">
            <button className="btn" type="button" onClick={closeDrawer}>
              Close
            </button>

            {canReassign(patient) && (
              <button
                className="btn btn-primary"
                type="button"
                onClick={() => {
                  setIsReassigning(true);
                  setSelectedDoctorId("");
                  setReassignError(null);
                }}
              >
                Reassign
              </button>
            )}
          </div>
        )}
      </aside>
    </>
  );
}
