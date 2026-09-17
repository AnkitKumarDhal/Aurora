import { LogOut, SunMedium } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import type { CurrentUser } from "@/types/api";

interface DoctorHeaderProps {
  user: CurrentUser | null;
  onLogout: () => void;
}

function getInitials(username: string | undefined): string {
  if (!username) {
    return "DR";
  }

  const parts = username
    .trim()
    .split(/[\s._-]+/)
    .filter(Boolean);

  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }

  return username.slice(0, 2).toUpperCase();
}

export default function DoctorHeader({ user, onLogout }: DoctorHeaderProps) {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const interval = window.setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => {
      window.clearInterval(interval);
    };
  }, []);

  function toggleTheme() {
    document.documentElement.classList.toggle("dark");
  }

  return (
    <header className="border-b border-border/70 bg-surface-alt/90 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-237.5 items-center justify-between px-5">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2.5">
            <span className="aurora-mark" />
            <span className="font-display text-[17px] font-semibold text-primary-dark">
              Aurora
            </span>
          </div>

          <span className="rounded-full bg-primary-tint px-3 py-1 text-xs font-semibold text-text-primary">
            General Medicine
          </span>
        </div>

        <div className="flex items-center gap-2">
          <time
            className="hidden text-xs font-medium text-text-secondary sm:block"
            dateTime={currentTime.toISOString()}
          >
            {currentTime.toLocaleTimeString("en-IN", {
              hour: "2-digit",
              minute: "2-digit",
              second: "2-digit",
            })}
          </time>

          <Button
            aria-label="Toggle theme"
            className="size-9 rounded-full text-text-secondary hover:bg-primary-tint hover:text-text-primary"
            onClick={toggleTheme}
            size="icon"
            type="button"
            variant="ghost"
          >
            <SunMedium className="size-4" />
          </Button>

          <div className="flex items-center gap-2 rounded-full border border-border bg-surface px-2 py-1.5">
            <span className="flex size-7 items-center justify-center rounded-full bg-primary-tint text-[11px] font-semibold text-text-primary">
              {getInitials(user?.username)}
            </span>

            <div className="hidden pr-2 sm:block">
              <p className="text-xs font-semibold text-text-primary">
                {user?.username ?? "Doctor"}
              </p>
              <p className="text-[10px] font-medium text-text-secondary">
                DOCTOR
              </p>
            </div>
          </div>

          <Button
            aria-label="Sign out"
            className="size-9 rounded-full text-text-secondary hover:bg-accent-tint hover:text-accent-dark"
            onClick={onLogout}
            size="icon"
            type="button"
            variant="ghost"
          >
            <LogOut className="size-4" />
          </Button>
        </div>
      </div>
    </header>
  );
}
