import { useNavigate } from "react-router-dom";
import { useMemo } from "react";

// Placeholder data — replace with GET /doctor/queue
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
  { border: string; badge: string; label: string }
> = {
  urgent: {
    border: "border-t-4 border-red-500",
    badge: "bg-red-100 text-red-700",
    label: "Urgent",
  },
  moderate: {
    border: "border-t-4 border-amber-400",
    badge: "bg-amber-100 text-amber-700",
    label: "Moderate",
  },
  routine: {
    border: "border-t-4 border-gray-300",
    badge: "bg-gray-100 text-gray-600",
    label: "Routine",
  },
};

function sortByPriority(patients: Patient[]): Patient[] {
  return [...patients].sort((a, b) => {
    const rankDiff = priorityRank[a.priority] - priorityRank[b.priority];
    if (rankDiff !== 0) return rankDiff;
    // within same priority tier, longer wait comes first
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
  const sortedPatients = useMemo(() => sortByPriority(mockPatients), []);
  const urgentCount = sortedPatients.filter(
    (p) => p.priority === "urgent",
  ).length;

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Patient Queue</h1>
        {urgentCount > 0 && (
          <span className="bg-red-100 text-red-700 text-sm font-semibold px-3 py-1 rounded-full">
            {urgentCount} urgent patient{urgentCount > 1 ? "s" : ""} waiting
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
        {sortedPatients.map((p) => {
          const style = priorityStyles[p.priority];
          return (
            <div
              key={p.id}
              onClick={() => navigate(`/patient/${p.id}`)}
              className={`bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow cursor-pointer ${style.border} overflow-hidden`}
            >
              <div className="p-4">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-11 h-11 rounded-full bg-gray-200 flex items-center justify-center font-semibold text-gray-600 shrink-0">
                    {initials(p.name)}
                  </div>
                  <div className="min-w-0">
                    <p className="font-semibold truncate">{p.name}</p>
                    <p className="text-xs text-gray-500">
                      {p.age} yrs · {p.gender}
                    </p>
                  </div>
                </div>

                <p className="text-sm text-gray-700 line-clamp-2 mb-3 min-h-[2.5rem]">
                  {p.complaint}
                </p>

                <div className="flex items-center justify-between">
                  <span
                    className={`text-xs font-semibold px-2 py-0.5 rounded-full ${style.badge}`}
                  >
                    {style.label}
                  </span>
                  <span className="text-xs text-gray-400">
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
