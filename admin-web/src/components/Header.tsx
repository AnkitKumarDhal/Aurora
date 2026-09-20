import { format } from "date-fns";
import { useEffect, useState } from "react";
import type { CurrentUser } from "@/api/auth";

interface HeaderProps {
  user: CurrentUser | null;
  onLogout: () => void;
}

export function Header({ user, onLogout }: HeaderProps) {
  const [clock, setClock] = useState(() => format(new Date(), "HH:mm:ss"));

  useEffect(() => {
    const timer = window.setInterval(() => {
      setClock(format(new Date(), "HH:mm:ss"));
    }, 1000);

    return () => window.clearInterval(timer);
  }, []);

  return (
    <header className="header">
      <div className="header-left">
        <div className="brand">
          <div className="brand-mark" />
          <div className="brand-name">AURORA</div>
        </div>

        <div className="dept-name">General Medicine</div>
      </div>

      <div className="header-right">
        <div className="live-indicator">
          <div className="live-dot" />
          <span>LIVE</span>
        </div>

        <div className="clock mono">{clock}</div>

        <div className="clock mono">{user?.username ?? "admin"}</div>

        <button className="btn" type="button" onClick={onLogout}>
          Sign out
        </button>
      </div>
    </header>
  );
}
