import { useEffect, useState } from "react";

export function useElapsedSeconds(
  initialSeconds: number | null,
  startedAt: string | null,
  shouldTick: boolean,
): number | null {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (!shouldTick) {
      return;
    }

    const interval = window.setInterval(() => {
      setNow(Date.now());
    }, 1000);

    return () => {
      window.clearInterval(interval);
    };
  }, [shouldTick]);

  if (initialSeconds === null) {
    return null;
  }

  if (!shouldTick || startedAt === null) {
    return initialSeconds;
  }

  const startedAtMs = Date.parse(startedAt);

  if (Number.isNaN(startedAtMs)) {
    return initialSeconds;
  }

  const elapsedSeconds = Math.floor((now - startedAtMs) / 1000);

  return Math.max(initialSeconds, elapsedSeconds);
}
