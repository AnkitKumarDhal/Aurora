import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { useAdminStore } from "@/store/adminStore";
import type { Patient } from "@/types/admin";

interface PatientDrawerProps {
  patients: Patient[];
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

function formatWait(patient: Patient): string {
  if (patient.state === "IN_CONSULTATION") {
    return "In session";
  }

  if (patient.waitingTimeSeconds === null) {
    return "—";
  }

  return `${Math.floor(patient.waitingTimeSeconds / 60)} min`;
}

export function PatientDrawer({ patients }: PatientDrawerProps) {
  const selectedPatientId = useAdminStore((state) => state.selectedPatientId);

  const isDrawerOpen = useAdminStore((state) => state.isDrawerOpen);

  const closeDrawer = useAdminStore((state) => state.closeDrawer);

  const [isPresented, setIsPresented] = useState(false);

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

  const isPriority = patient.urgencyLevel !== null && patient.urgencyLevel >= 4;

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
                className={cn("drawer-status-badge", isPriority && "priority")}
              >
                {isPriority ? "High Priority" : "Normal"}
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

                <div className="drawer-field-value">{formatWait(patient)}</div>
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

        <div className="drawer-actions">
          <button className="btn" type="button" onClick={closeDrawer}>
            Close
          </button>
        </div>
      </aside>
    </>
  );
}
