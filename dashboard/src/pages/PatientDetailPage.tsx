import { useParams, useNavigate } from "react-router-dom";
import {
  ChevronLeft,
  Check,
  Pencil,
  X,
  Image as ImageIcon,
  TrendingUp,
} from "lucide-react";

export default function PatientDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background p-6 pb-28 relative max-w-2xl mx-auto">
      <button
        className="size-10 rounded-full bg-muted text-primary flex items-center justify-center mb-4"
        onClick={() => navigate("/queue")}
        aria-label="Back to queue"
      >
        <ChevronLeft className="size-5" />
      </button>

      {/* TODO (Phase 3): fetch GET /doctor/patients/{id}, replace the mock content below */}
      <h1 className="text-2xl font-extrabold text-primary">Patient #{id}</h1>
      <p className="text-muted-foreground mb-6">Age — · Complaint —</p>

      <div className="bg-card border border-border rounded-2xl p-5 mb-4">
        <h2 className="font-bold text-primary mb-2">Symptoms</h2>
        <ul className="list-disc list-inside text-sm text-foreground/80 space-y-1">
          <li>—</li>
        </ul>
      </div>

      <div className="bg-card border border-border rounded-2xl p-5 mb-4">
        <h2 className="font-bold text-primary mb-3">Past reports</h2>
        <div className="flex gap-3">
          <span className="size-16 rounded-xl bg-muted flex items-center justify-center">
            <ImageIcon className="size-5 text-primary" />
          </span>
          <span className="size-16 rounded-xl bg-muted flex items-center justify-center">
            <ImageIcon className="size-5 text-primary" />
          </span>
          <span className="size-16 rounded-xl bg-muted flex items-center justify-center">
            <TrendingUp className="size-5 text-primary" />
          </span>
        </div>
      </div>

      <div className="bg-card border border-border rounded-2xl p-5">
        <h2 className="font-bold text-primary mb-2">AI summary</h2>
        <ul className="list-disc list-inside text-sm text-foreground/80 space-y-1">
          <li>—</li>
        </ul>
      </div>

      {/* Approve/Edit/Reject — not wired to a real endpoint yet, that's Phase 3 */}
      <div className="fixed bottom-0 left-0 right-0 bg-background border-t border-border p-4">
        <div className="max-w-2xl mx-auto flex gap-3">
          <button className="flex-1 bg-primary text-primary-foreground rounded-xl py-3 font-bold flex items-center justify-center gap-2">
            <Check className="size-4" /> Confirm
          </button>
          <button className="flex-1 bg-muted text-primary rounded-xl py-3 font-bold flex items-center justify-center gap-2">
            <Pencil className="size-4" /> Edit
          </button>
          <button className="flex-1 bg-destructive/10 text-destructive rounded-xl py-3 font-bold flex items-center justify-center gap-2">
            <X className="size-4" /> Reject
          </button>
        </div>
      </div>
    </div>
  );
}
