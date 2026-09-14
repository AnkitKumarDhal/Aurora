import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth, homeRouteForRole } from "@/lib/auth";
import { OnboardingProvider } from "@/lib/onboarding";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import WelcomePage from "./pages/onboarding/WelcomePage";
import LocationPage from "./pages/onboarding/LocationPage";
import LanguagePage from "./pages/onboarding/LanguagePage";
import RolePage from "./pages/onboarding/RolePage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import QueuePage from "./pages/QueuePage";
import PatientDetailPage from "./pages/PatientDetailPage";
import PatientHomePage from "./pages/PatientHomePage";

function RootRedirect() {
  const { token, role } = useAuth();
  return (
    <Navigate
      to={token ? homeRouteForRole(role) : "/onboarding/welcome"}
      replace
    />
  );
}

function App() {
  return (
    <AuthProvider>
      <OnboardingProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<RootRedirect />} />

            <Route path="/onboarding/welcome" element={<WelcomePage />} />
            <Route path="/onboarding/location" element={<LocationPage />} />
            <Route path="/onboarding/language" element={<LanguagePage />} />
            <Route path="/onboarding/role" element={<RolePage />} />

            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            <Route
              path="/queue"
              element={
                <ProtectedRoute role="doctor">
                  <QueuePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/patient/:id"
              element={
                <ProtectedRoute role="doctor">
                  <PatientDetailPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/my-summary"
              element={
                <ProtectedRoute role="patient">
                  <PatientHomePage />
                </ProtectedRoute>
              }
            />
          </Routes>
        </BrowserRouter>
      </OnboardingProvider>
    </AuthProvider>
  );
}

export default App;
