import { useEffect } from "react";

import { Header } from "@/components/Header";
import { PatientBoard } from "@/components/PatientBoard";
import { PatientDrawer } from "@/components/PatientDrawer";
import { DoctorsPanel } from "@/components/DoctorsPanel";
import { PromotionPanel } from "@/components/PromotionPanel";
import { StatsStrip } from "@/components/StatsStrip";
import { Toast } from "@/components/Toast";
import LoginPage from "@/pages/LoginPage";

import { useAdminDashboard } from "@/features/dashboard/useAdminDashboard";

import { useAuth } from "@/auth/useAuth";

import { initializeAuth } from "@/auth/store";

export default function App() {
  const { user, isLoading: authLoading, isAuthenticated, logout } = useAuth();

  useEffect(() => {
    void initializeAuth();
  }, []);

  const dashboard = useAdminDashboard(isAuthenticated);

  if (authLoading) {
    return (
      <main className="login-page">
        <p>Loading...</p>
      </main>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  if (dashboard.isLoading && !dashboard.dashboard) {
    return (
      <main className="login-page">
        <p>Loading dashboard...</p>
      </main>
    );
  }

  if (dashboard.error && !dashboard.dashboard) {
    return (
      <main className="login-page">
        <p>{dashboard.error}</p>
      </main>
    );
  }

  if (!dashboard.dashboard) {
    return null;
  }

  return (
    <div className="app">
      <Header user={user} onLogout={logout} />

      <StatsStrip stats={dashboard.dashboard.stats} />

      <div className="main">
        <PatientBoard patients={dashboard.dashboard.patients} />

        <aside className="sidebar">
          <DoctorsPanel doctors={dashboard.dashboard.doctors} />

          <PromotionPanel
            promotions={dashboard.dashboard.promotions}
            onResolved={dashboard.reload}
          />
        </aside>
      </div>

      <PatientDrawer
        patients={dashboard.dashboard.patients}
        doctors={dashboard.dashboard.doctors}
        onReassigned={dashboard.reload}
      />

      <Toast />
    </div>
  );
}
