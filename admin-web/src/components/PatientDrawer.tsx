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

  const [reassignPatientId, setReassignPatientId] = useState<string | null>(
    null,
  );

  const [selectedDoctorId, setSelectedDoctorId] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);

  const [reassignError, setReassignError] = useState<string | null>(null);

  const patient = patients.find((item) => item.id === selectedPatientId);

  const isReassigning =
    patient !== undefined && reassignPatientId === patient.id;

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      setIsPresented(isDrawerOpen);
    });

    return () => {
      window.cancelAnimationFrame(frame);
    };
  }, [isDrawerOpen]);

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

  const currentPatient = patient;

  const isPriority =
    currentPatient.urgencyLevel !== null &&
    currentPatient.urgencyLevel >= 4 &&
    currentPatient.state !== "COMPLETED" &&
    currentPatient.state !== "CANCELLED";

  const isPast =
    currentPatient.state === "COMPLETED" ||
    currentPatient.state === "CANCELLED";

  async function handleConfirmReassign(): Promise<void> {
    if (!selectedDoctorId || isSubmitting) {
      return;
    }

    setIsSubmitting(true);
    setReassignError(null);

    try {
      const result = await reassignPatient(
        currentPatient.queueEntryId,
        selectedDoctorId,
      );

      const targetDoctor = doctors.find(
        (doctor) => doctor.id === result.doctor_id,
      );

      showToast(
        `Reassigned ${currentPatient.name} to ${
          targetDoctor?.name ?? result.doctor_id
        }`,
        "success",
      );

      setReassignPatientId(null);
      setSelectedDoctorId("");
      setReassignError(null);
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

  function openReassignPanel(): void {
    setReassignPatientId(currentPatient.id);
    setSelectedDoctorId("");
    setReassignError(null);
  }

  function closeReassignPanel(): void {
    setReassignPatientId(null);
    setSelectedDoctorId("");
    setReassignError(null);
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
            <div className="drawer-patient-id">{currentPatient.id}</div>

            <div
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: "11px",
                color: "var(--color-text-secondary)",
                marginTop: "4px",
              }}
            >
              {currentPatient.name}

              {currentPatient.age !== null && ` · ${currentPatient.age}`}
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
                  {currentPatient.state.replaceAll("_", " ")}
                </span>
              </div>
            </div>

            <div>
              <div className="drawer-section-title">Details</div>

              <div className="drawer-row">
                <div className="drawer-field">
                  <div className="drawer-field-label">Wait Time</div>

                  <div className="drawer-field-value">
                    {currentPatient.state === "IN_CONSULTATION"
                      ? "In session"
                      : formatWait(currentPatient.waitingTimeSeconds)}
                  </div>
                </div>

                <div className="drawer-field">
                  <div className="drawer-field-label">Assigned</div>

                  <div className="drawer-field-value">
                    {currentPatient.doctor ?? "Unassigned"}
                  </div>
                </div>

                <div className="drawer-field">
                  <div className="drawer-field-label">Urgency</div>

                  <div className="drawer-field-value">
                    {currentPatient.urgencyLevel !== null
                      ? `Level ${currentPatient.urgencyLevel}`
                      : "—"}
                  </div>
                </div>

                <div className="drawer-field">
                  <div className="drawer-field-label">Priority Score</div>

                  <div className="drawer-field-value">
                    {currentPatient.priorityScore ?? "—"}
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
                {currentPatient.complaint ?? "No complaint recorded."}
              </div>
            </div>

            <div>
              <div className="drawer-section-title">Timeline</div>

              <div className="timeline">
                <div className="timeline-item">
                  <div>Entered queue</div>

                  <div className="timeline-time">
                    {formatTime(currentPatient.queuedAt)}
                  </div>
                </div>

                <div className="timeline-item">
                  <div>
                    {currentPatient.doctor
                      ? `Assigned to ${currentPatient.doctor}`
                      : "Awaiting doctor assignment"}
                  </div>
                </div>

                <div className="timeline-item current">
                  <div>
                    Current state: {currentPatient.state.replaceAll("_", " ")}
                  </div>
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
                  {currentPatient.doctor ?? "Unassigned"}
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
                  const isCurrent = doctor.id === currentPatient.doctorId;

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
                onClick={closeReassignPanel}
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

            {canReassign(currentPatient) && (
              <button
                className="btn btn-primary"
                type="button"
                onClick={openReassignPanel}
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
