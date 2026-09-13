import { useParams, useNavigate } from "react-router-dom";

export default function PatientDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <button className="text-blue-600 mb-4" onClick={() => navigate("/queue")}>
        ← Back to Queue
      </button>
      <h1 className="text-2xl font-bold mb-4">Patient #{id}</h1>
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-500">
          Structured summary, conversation, and documents will render here.
        </p>
        {/* TODO: fetch GET /doctor/patients/{id}, render chief complaint / HPI / etc. */}
      </div>
    </div>
  );
}
