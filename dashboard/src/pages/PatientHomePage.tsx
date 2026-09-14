import { useNavigate } from "react-router-dom";
import { useAuth } from "@/lib/auth";

export default function PatientHomePage() {
  const { loginId, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-extrabold text-primary">Aurora</h1>
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
      <div className="bg-card border border-border rounded-2xl p-6">
        <p className="text-muted-foreground">
          Signed in as{" "}
          <span className="font-mono text-foreground">{loginId}</span>. Your
          session history and summaries will appear here.
        </p>
      </div>
    </div>
  );
}
