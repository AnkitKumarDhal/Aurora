import { format } from "date-fns";
import { useEffect, useState } from "react";

export function Header() {
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
      </div>
    </header>
  );
}
