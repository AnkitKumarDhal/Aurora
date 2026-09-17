import { useAuth } from "@/auth/useAuth";

export default function QueuePage() {
  const { user, logout } = useAuth();

  return (
    <main className="min-h-screen bg-background p-6">
      <div className="mx-auto max-w-6xl">
        <div className="flex items-center justify-between rounded-xl border bg-card p-6">
          <div>
            <p className="text-sm text-muted-foreground">Signed in as</p>
            <h1 className="text-2xl font-semibold">{user?.username}</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Doctor ID: {user?.actor_id}
            </p>
          </div>

          <button
            className="rounded-md border px-4 py-2 text-sm font-medium transition hover:bg-accent"
            onClick={logout}
            type="button"
          >
            Sign out
          </button>
        </div>
      </div>
    </main>
  );
}
