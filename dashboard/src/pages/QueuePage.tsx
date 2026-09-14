import { useNavigate } from "react-router-dom";
import { useMemo } from "react";
import { AlertTriangle } from "lucide-react";
import { useAuth } from "@/lib/auth";

type Patient = {
  id: string;
  name: string;
  age: number;
  gender: string;
  complaint: string;
  redFlag: boolean;
  priority: "urgent" | "moderate" | "routine";
  waitMinutes: number;
  checkedInAt: string;
};

const mockPatients: Patient[] = [
  {
    id: "1",
    name: "Ramesh Kumar",
    age: 58,
    gender: "M",
    complaint: "Chest pain, radiating to left arm",
    redFlag: true,
    priority: "urgent",
    waitMinutes: 4,
    checkedInAt: "10:42 AM",
  },
  {
    id: "2",
    name: "Sita Devi",
    age: 34,
    gender: "F",
    complaint: "Fever, cough for 3 days",
    redFlag: false,
    priority: "routine",
    waitMinutes: 22,
    checkedInAt: "10:24 AM",
  },
  {
    id: "3",
    name: "Arjun Singh",
    age: 45,
    gender: "M",
    complaint: "Abdominal pain, moderate",
    redFlag: false,
    priority: "moderate",
    waitMinutes: 15,
    checkedInAt: "10:31 AM",
  },
  {
    id: "4",
    name: "Priya Nair",
    age: 29,
    gender: "F",
    complaint: "Severe headache, dizziness",
    redFlag: true,
    priority: "urgent",
    waitMinutes: 2,
    checkedInAt: "10:44 AM",
  },
  {
    id: "5",
    name: "Manoj Yadav",
    age: 67,
    gender: "M",
    complaint: "Routine follow-up, diabetes",
    redFlag: false,
    priority: "routine",
    waitMinutes: 35,
    checkedInAt: "10:11 AM",
  },
  {
    id: "6",
    name: "Fatima Sheikh",
    age: 51,
    gender: "F",
    complaint: "Joint pain, swelling",
    redFlag: false,
    priority: "moderate",
    waitMinutes: 18,
    checkedInAt: "10:28 AM",
  },
];

const priorityRank: Record<Patient["priority"], number> = {
  urgent: 0,
  moderate: 1,
  routine: 2,
};

const priorityStyles: Record<
  Patient["priority"],
  { border: string; badge: string; label: string; tint: string }
> = {
  urgent: {
    border: "border-t-4 border-destructive",
    badge: "bg-destructive/15 text-destructive",
    label: "Urgent",
    tint: "bg-destructive/5",
  },
  moderate: {
    border: "border-t-4 border-accent",
    badge: "bg-accent/15 text-accent",
    label: "Moderate",
    tint: "",
  },
  routine: {
    border: "border-t-4 border-border",
    badge: "bg-muted text-muted-foreground",
    label: "Routine",
    tint: "",
  },
};

function sortByPriority(patients: Patient[]): Patient[] {
  return [...patients].sort((a, b) => {
    const rankDiff = priorityRank[a.priority] - priorityRank[b.priority];
    if (rankDiff !== 0) return rankDiff;
    return b.waitMinutes - a.waitMinutes;
  });
}

function initials(name: string) {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

export default function QueuePage() {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const sortedPatients = useMemo(() => sortByPriority(mockPatients), []);
  const urgentCount = sortedPatients.filter(
    (p) => p.priority === "urgent",
  ).length;

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-extrabold text-primary">Patient Queue</h1>
        <div className="flex items-center gap-3">
          {urgentCount > 0 && (
            <span className="bg-destructive/15 text-destructive text-sm font-bold px-3 py-1 rounded-full">
              {urgentCount} urgent patient{urgentCount > 1 ? "s" : ""} waiting
            </span>
          )}
          <button
            className="text-sm text-muted-foreground hover:text-foreground"
            onClick={() => {
              logout();
              navigate("/login");
            }}
          >
            Log out
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
        {sortedPatients.map((p) => {
          const style = priorityStyles[p.priority];
          return (
            <div
              key={p.id}
              onClick={() => navigate(`/patient/${p.id}`)}
              className={`relative bg-card rounded-2xl shadow-sm hover:shadow-md transition-shadow cursor-pointer ${style.border} ${style.tint} overflow-hidden`}
            >
              {p.priority === "urgent" && (
                <span className="absolute top-3 right-3 size-6 rounded-full bg-destructive text-white flex items-center justify-center">
                  <AlertTriangle className="size-3.5" />
                </span>
              )}
              <div className="p-4">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-11 h-11 rounded-full bg-muted flex items-center justify-center font-bold text-primary shrink-0">
                    {initials(p.name)}
                  </div>
                  <div className="min-w-0">
                    <p className="font-bold truncate text-foreground">
                      {p.name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {p.age} yrs · {p.gender}
                    </p>
                  </div>
                </div>
                <p className="text-sm text-foreground/80 line-clamp-2 mb-3 min-h-[2.5rem]">
                  {p.complaint}
                </p>
                <div className="flex items-center justify-between">
                  <span
                    className={`text-xs font-bold px-2 py-0.5 rounded-full ${style.badge}`}
                  >
                    {style.label}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    waiting {p.waitMinutes} min
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
