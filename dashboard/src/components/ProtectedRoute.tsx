import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useAuth, homeRouteForRole } from "@/lib/auth";
import type { Role } from "@/lib/api";

export function ProtectedRoute({
  children,
  role,
}: {
  children: ReactNode;
  role?: Role;
}) {
  const { token, role: currentRole } = useAuth();

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (role && currentRole !== role) {
    // logged in, but wrong role for this route — bounce to their own home
    return <Navigate to={homeRouteForRole(currentRole)} replace />;
  }

  return <>{children}</>;
}
