import { SunMedium } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { CurrentUser } from "@/types/api";

interface DoctorHeaderProps {
  user: CurrentUser | null;
  onLogout: () => void;
  showThemeToggle?: boolean;
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

export default function DoctorHeader({
  user,
  onLogout,
  showThemeToggle = false,
}: DoctorHeaderProps) {
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
    <header className="sticky top-0 z-20 border-b border-border bg-surface/90 backdrop-blur-[10px]">
      <div className="flex items-center justify-between gap-4 px-7 py-3.25">
        <div className="flex items-center gap-3.5">
          <div className="flex items-center gap-2.5">
            <span className="aurora-mark" />
            <span className="font-display text-[17px] font-medium text-primary-dark">
              Aurora
            </span>
          </div>

          <span className="rounded-full bg-primary-tint px-3 py-1.5 text-xs font-bold text-primary-dark">
            General Medicine
          </span>
        </div>

        <div className="flex items-center gap-3.5">
          <time
            className="hidden text-xs font-medium tabular-nums text-text-secondary sm:block"
            dateTime={currentTime.toISOString()}
          >
            {currentTime.toLocaleTimeString("en-IN", {
              hour: "2-digit",
              minute: "2-digit",
              second: "2-digit",
            })}
          </time>

          {showThemeToggle && (
            <Button
              aria-label="Toggle theme"
              className="size-[34px] rounded-full border border-border bg-surface-alt text-text-secondary hover:bg-primary-tint hover:text-primary-dark"
              onClick={toggleTheme}
              size="icon"
              type="button"
              variant="ghost"
            >
              <SunMedium className="size-4" />
            </Button>
          )}

          <DropdownMenu modal={false}>
            <DropdownMenuTrigger
              render={
                <button
                  className="flex items-center gap-2.5 rounded-full border border-border bg-surface-alt py-1 pl-2 pr-3 transition-colors hover:border-primary/70 hover:bg-primary-tint/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
                  type="button"
                />
              }
            >
              <span className="flex size-[30px] shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-primary-tint to-accent-tint text-xs font-extrabold text-primary-dark">
                {getInitials(user?.username)}
              </span>

              <span className="hidden text-left sm:block">
                <span className="block text-[13px] font-bold text-text-primary">
                  {user?.username ?? "Doctor"}
                </span>

                <span className="block text-[11px] text-text-secondary">
                  DOCTOR
                </span>
              </span>
            </DropdownMenuTrigger>

            <DropdownMenuContent
              align="end"
              className="min-w-44 rounded-xl border-border bg-surface p-1.5 shadow-[0_18px_40px_-18px_rgba(58,46,92,0.45)]"
              sideOffset={8}
            >
              <DropdownMenuItem
                className="cursor-pointer rounded-lg px-3 py-2 text-xs font-semibold text-danger focus:bg-accent-tint focus:text-accent-dark"
                onSelect={() => {
                  onLogout();
                }}
              >
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
}
