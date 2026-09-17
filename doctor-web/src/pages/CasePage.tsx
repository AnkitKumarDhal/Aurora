import { useParams } from "react-router-dom";

export default function CasePage() {
  const { sessionId } = useParams<{ sessionId: string }>();

  return (
    <main className="flex min-h-screen items-center justify-center bg-background p-6">
      <section className="rounded-2xl border bg-card p-8 text-center shadow-sm">
        <h1 className="text-2xl font-semibold">Patient case</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Session: {sessionId}
        </p>
      </section>
    </main>
  );
}
