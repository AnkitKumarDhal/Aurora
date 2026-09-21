import { Bot, Headphones, MessageSquare, User } from "lucide-react";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getApiErrorMessage } from "@/api/client";
import { getConversationHistory } from "@/api/conversation";
import type { ConversationTurn } from "@/types/api";

function formatTime(value: string): string {
  return new Date(value).toLocaleString("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function speakerLabel(speaker: string): string {
  if (speaker === "system") {
    return "Aurora AI";
  }

  if (speaker === "patient") {
    return "Patient";
  }

  return speaker;
}

function turnStyle(speaker: string): {
  container: string;
  iconBackground: string;
  iconColor: string;
} {
  if (speaker === "patient") {
    return {
      container: "border-accent/40 bg-accent-tint/35",
      iconBackground: "bg-accent-tint",
      iconColor: "text-accent-dark",
    };
  }

  return {
    container: "border-primary/25 bg-primary-tint/30",
    iconBackground: "bg-primary-tint",
    iconColor: "text-primary-dark",
  };
}

function Turn({ turn }: { turn: ConversationTurn }) {
  const isPatient = turn.speaker === "patient";

  const style = turnStyle(turn.speaker);

  return (
    <div className={`rounded-xl border px-3.5 py-3 ${style.container}`}>
      <div className="flex items-start gap-3">
        <span
          className={`flex size-8 shrink-0 items-center justify-center rounded-full ${style.iconBackground}`}
        >
          {isPatient ? (
            <User className={`size-4 ${style.iconColor}`} />
          ) : (
            <Bot className={`size-4 ${style.iconColor}`} />
          )}
        </span>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <span className="text-[12px] font-extrabold text-text-primary">
              {speakerLabel(turn.speaker)}
            </span>

            <span className="text-[10px] text-text-secondary">
              {formatTime(turn.created_at)}
            </span>

            <span className="rounded-full bg-surface px-2 py-0.5 text-[9.5px] font-bold uppercase tracking-wide text-text-secondary">
              {turn.input_type.toLowerCase()}
            </span>

            {turn.language && (
              <span className="rounded-full bg-surface px-2 py-0.5 text-[9.5px] font-bold text-text-secondary">
                {turn.language}
              </span>
            )}
          </div>

          <p className="mt-2 whitespace-pre-wrap text-[12.5px] leading-[1.65] text-text-primary">
            {turn.content || "No transcript content recorded."}
          </p>
        </div>
      </div>
    </div>
  );
}

export default function ConversationPanel({
  sessionId,
}: {
  sessionId: string;
}) {
  const [turns, setTurns] = useState<ConversationTurn[]>([]);

  const [isLoading, setIsLoading] = useState(true);

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    void getConversationHistory(sessionId)
      .then((response) => {
        if (cancelled) {
          return;
        }

        setTurns(response.turns);
      })
      .catch((requestError) => {
        if (cancelled) {
          return;
        }

        setError(
          getApiErrorMessage(
            requestError,
            "Unable to load the interview conversation.",
          ),
        );
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  return (
    <Card className="mt-4 rounded-[20px] border border-border bg-surface p-0 shadow-none">
      <CardHeader className="flex flex-row items-center justify-between gap-3 px-5.5 pb-0 pt-5">
        <div className="flex items-center gap-2.5">
          <span className="flex size-8 items-center justify-center rounded-lg bg-primary-tint text-primary-dark">
            <MessageSquare className="size-4" />
          </span>

          <div>
            <CardTitle className="font-display text-[15.5px] font-semibold text-primary-dark">
              Patient · AI conversation
            </CardTitle>

            <p className="mt-0.5 text-[10.5px] text-text-secondary">
              Exact persisted kiosk interaction for clinical verification.
            </p>
          </div>
        </div>

        {!isLoading && (
          <span className="rounded-full bg-surface-alt px-2.5 py-1 text-[10px] font-extrabold text-text-secondary">
            {turns.length} {turns.length === 1 ? "turn" : "turns"}
          </span>
        )}
      </CardHeader>

      <CardContent className="px-5.5 pb-5 pt-3.5">
        {isLoading ? (
          <div className="flex min-h-35 items-center justify-center">
            <div className="flex items-center gap-2 text-xs font-semibold text-text-secondary">
              <Headphones className="size-4" />
              Loading conversation
            </div>
          </div>
        ) : error ? (
          <div className="rounded-xl border border-danger/30 bg-accent-tint px-4 py-3 text-[12px] text-danger">
            {error}
          </div>
        ) : turns.length === 0 ? (
          <div className="rounded-xl border border-border bg-surface-alt px-4 py-8 text-center text-[12px] text-text-secondary">
            No conversation turns were recorded for this session.
          </div>
        ) : (
          <div className="max-h-125 space-y-2.5 overflow-y-auto pr-1">
            {turns.map((turn) => (
              <Turn key={turn.turn_id} turn={turn} />
            ))}
          </div>
        )}

        <div className="mt-3 rounded-lg border border-border bg-surface-alt px-3 py-2.5 text-[10.5px] leading-relaxed text-text-secondary">
          This panel shows the stored conversation text exactly as received by
          Aurora. Voice interactions currently show the speech transcript; the
          raw microphone audio itself is not persisted.
        </div>
      </CardContent>
    </Card>
  );
}
