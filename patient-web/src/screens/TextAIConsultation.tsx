import { useEffect, useRef, useState } from "react";
import type { ClinicalIntelligenceTurnResponse } from "@/api/clinicalIntelligence";
import { Bot, Send, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { loadPatientDraft } from "@/lib/patientDraft";

interface TextAIConsultationProps {
  draftId: string;
  onNext: () => void;
  onConversationTurn: (
    inputType: "TEXT",
    content: string,
    language: string,
  ) => Promise<ClinicalIntelligenceTurnResponse | null>;
  language: "en" | "hi";
}

interface Message {
  id: string;
  sender: "ai" | "user";
  text: string;
}

function getInitialMessages(draftId: string, isHi: boolean): Message[] {
  const initialMessage: Message = {
    id: "initial",
    sender: "ai",
    text: isHi
      ? "नमस्ते! मैं औरोरा AI हूं। कृपया अपने लक्षण बताएं।"
      : "Hello! I am Aurora AI. Please describe your symptoms.",
  };

  const draft = loadPatientDraft();

  if (!draft || draft.draft_id !== draftId) {
    return [initialMessage];
  }

  const existingTurns = draft.conversation_turns.filter(
    (turn) => turn.input_type === "TEXT",
  );

  if (existingTurns.length === 0) {
    return [initialMessage];
  }

  return [
    initialMessage,
    ...existingTurns.map((turn) => ({
      id: turn.local_id,
      sender: "user" as const,
      text: turn.content,
    })),
  ];
}

function getInitialMessageCount(draftId: string): number {
  const draft = loadPatientDraft();

  if (!draft || draft.draft_id !== draftId) {
    return 0;
  }

  return draft.conversation_turns.filter((turn) => turn.input_type === "TEXT")
    .length;
}

export function TextAIConsultation({
  draftId,
  onNext,
  onConversationTurn,
  language,
}: TextAIConsultationProps) {
  const isHi = language === "hi";
  const initialMessageCount = getInitialMessageCount(draftId);

  const [messages, setMessages] = useState<Message[]>(() =>
    getInitialMessages(draftId, isHi),
  );
  const [input, setInput] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [canContinue, setCanContinue] = useState(initialMessageCount > 0);
  const [error, setError] = useState<string | null>(null);

  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isThinking]);

  const handleSend = async () => {
    const content = input.trim();

    if (!content || isThinking) {
      return;
    }

    setError(null);
    setIsThinking(true);

    setMessages((previous) => [
      ...previous,
      {
        id: `user-${Date.now()}`,
        sender: "user",
        text: content,
      },
    ]);

    setInput("");

    const response = await onConversationTurn(
      "TEXT",
      content,
      isHi ? "hi" : "en",
    );

    if (!response) {
      setError(
        isHi
          ? "उत्तर प्राप्त नहीं हो सका। कृपया फिर से प्रयास करें।"
          : "The AI could not process your response. Please try again.",
      );
      setIsThinking(false);
      return;
    }

    const assistantResponse = response.assistant_response;

    if (assistantResponse?.trim()) {
      setMessages((previous) => [
        ...previous,
        {
          id: `ai-${response.turn_id}`,
          sender: "ai",
          text: assistantResponse,
        },
      ]);
    }

    setCanContinue(response.completed);
    setIsThinking(false);
  };

  return (
    <div className="flex h-[80vh] w-full flex-col items-center">
      <div className="mb-4 text-center">
        <h2 className="text-2xl font-bold text-text-primary">
          {isHi ? "AI टेक्स्ट परामर्श" : "AI Text Consultation"}
        </h2>

        <p className="text-sm text-text-secondary">
          {isHi
            ? "अपने लक्षण टाइप करें और एंटर दबाएं"
            : "Type your symptoms and press Enter"}
        </p>
      </div>

      <div className="flex w-full max-w-3xl flex-1 flex-col overflow-hidden rounded-xl border-2 border-border bg-surface p-4 shadow-sm">
        <div className="mb-4 flex-1 space-y-3 overflow-y-auto pr-2">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex items-start gap-3 ${
                message.sender === "user" ? "justify-end" : ""
              }`}
            >
              {message.sender === "ai" && (
                <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-primary-tint">
                  <Bot className="h-4 w-4 text-primary-dark" />
                </div>
              )}

              <div
                className={`max-w-[80%] rounded-xl p-3 text-base ${
                  message.sender === "ai"
                    ? "rounded-tl-none bg-primary-tint text-text-primary"
                    : "rounded-tr-none bg-accent-tint text-text-primary"
                }`}
              >
                {message.text}
              </div>

              {message.sender === "user" && (
                <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-accent-tint">
                  <User className="h-4 w-4 text-accent-dark" />
                </div>
              )}
            </div>
          ))}

          {isThinking && (
            <div className="flex items-start gap-3">
              <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-primary-tint">
                <Bot className="h-4 w-4 text-primary-dark" />
              </div>

              <div className="flex gap-1 rounded-xl rounded-tl-none bg-primary-tint p-3">
                <span className="h-2 w-2 animate-bounce rounded-full bg-text-secondary" />
                <span
                  className="h-2 w-2 animate-bounce rounded-full bg-text-secondary"
                  style={{ animationDelay: "0.2s" }}
                />
                <span
                  className="h-2 w-2 animate-bounce rounded-full bg-text-secondary"
                  style={{ animationDelay: "0.4s" }}
                />
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {error && (
          <div className="mb-3 rounded-xl border-2 border-danger bg-surface px-4 py-3 text-sm font-semibold text-danger">
            {error}
          </div>
        )}

        <div className="flex gap-3">
          <input
            className="flex-1 rounded-lg border-2 border-border bg-bg p-4 text-lg text-text-primary focus:border-primary focus:outline-none"
            disabled={isThinking}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                handleSend();
              }
            }}
            placeholder={
              isHi ? "अपने लक्षण यहां टाइप करें..." : "Type your symptoms here..."
            }
            value={input}
          />

          <Button
            className="rounded-lg bg-primary-dark px-6 py-4 text-lg text-white shadow-lg hover:bg-text-primary"
            disabled={isThinking || !input.trim()}
            onClick={handleSend}
          >
            <Send className="h-5 w-5" />
          </Button>
        </div>
      </div>

      <Button
        className="mt-4 rounded-lg bg-primary-dark px-10 py-5 text-lg text-white shadow-lg transition-all hover:bg-text-primary"
        disabled={isThinking || !canContinue}
        onClick={onNext}
      >
        {isHi ? "अगला: रिपोर्ट अपलोड" : "Next: Upload Reports"}
      </Button>
    </div>
  );
}
