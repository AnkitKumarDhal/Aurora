import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DoctorCaseResponse } from "@/types/api";
import { formatDate } from "../utils";

export default function IdentityPanel({
  patient,
}: {
  patient: DoctorCaseResponse["patient"];
}) {
  if (!patient) {
    return null;
  }

  const rows = [
    ["Patient ID", patient.patient_id],
    ["Date of birth", formatDate(patient.date_of_birth)],
    ["ABHA reference", patient.abha_reference ?? "Not linked"],
    ["Hospital reference", patient.hospital_reference ?? "—"],
  ];

  return (
    <Card className="mt-4 rounded-[20px] border border-border bg-surface p-0 shadow-none">
      <CardHeader className="px-[22px] pb-0 pt-5">
        <CardTitle className="font-display text-[15.5px] font-semibold text-primary-dark">
          Patient identity
        </CardTitle>
      </CardHeader>

      <CardContent className="px-[22px] pb-5 pt-[14px]">
        {rows.map(([label, value], index) => (
          <div
            className={[
              "flex items-center justify-between gap-4 py-2 text-[13px]",
              index === rows.length - 1
                ? "border-b-0 pb-0"
                : "border-b border-border",
            ].join(" ")}
            key={label}
          >
            <span className="text-text-secondary">{label}</span>

            <span className="text-right font-bold text-text-primary">
              {value}
            </span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
