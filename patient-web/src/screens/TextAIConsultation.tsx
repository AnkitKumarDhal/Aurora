import { useEffect, useRef, useState } from "react";
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
  ) => boolean;
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
  const messageCount = useRef(initialMessageCount);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isThinking]);

  const handleSend = () => {
    const content = input.trim();

    if (!content || isThinking) {
      return;
    }

    setError(null);
    setIsThinking(true);

    const saved = onConversationTurn("TEXT", content, isHi ? "hi" : "en");

    if (!saved) {
      setError("Unable to save your response locally.");
      setIsThinking(false);
      return;
    }

    messageCount.current += 1;

    setMessages((previous) => [
      ...previous,
      {
        id: `user-${messageCount.current}`,
        sender: "user",
        text: content,
      },
    ]);

    setInput("");
    setCanContinue(true);

    window.setTimeout(() => {
      const questions = [
        isHi ? "कब से ये लक्षण हैं?" : "How long have you had these symptoms?",
        isHi ? "क्या कोई अन्य लक्षण हैं?" : "Are there any other symptoms?",
        isHi ? "क्या आप कोई दवा ले रहे हैं?" : "Are you taking any medications?",
        isHi
          ? "क्या आपको कोई पुरानी बीमारी है?"
          : "Do you have any chronic illnesses?",
        isHi
          ? "धन्यवाद। आप अब अपनी रिपोर्ट अपलोड कर सकते हैं।"
          : "Thank you. You can now proceed to upload your reports.",
      ];

      const questionIndex = Math.min(
        messageCount.current - 1,
        questions.length - 1,
      );

      setMessages((previous) => [
        ...previous,
        {
          id: `ai-${messageCount.current}`,
          sender: "ai",
          text: questions[questionIndex],
        },
      ]);

      setIsThinking(false);
    }, 1500);
  };

  return (
    <div className="flex h-[80vh] w-full flex-col items-center">
      <div className="mb-4 text-center">
        <h2 className="text-2xl font-bold text-[var(--color-text-primary)]">
          {isHi ? "AI टेक्स्ट परामर्श" : "AI Text Consultation"}
        </h2>

        <p className="text-sm text-[var(--color-text-secondary)]">
          {isHi
            ? "अपने लक्षण टाइप करें और एंटर दबाएं"
            : "Type your symptoms and press Enter"}
        </p>
      </div>

      <div className="flex w-full max-w-3xl flex-1 flex-col overflow-hidden rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-sm">
        <div className="mb-4 flex-1 space-y-3 overflow-y-auto pr-2">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex items-start gap-3 ${
                message.sender === "user" ? "justify-end" : ""
              }`}
            >
              {message.sender === "ai" && (
                <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-[var(--color-primary-tint)]">
                  <Bot className="h-4 w-4 text-[var(--color-primary-dark)]" />
                </div>
              )}

              <div
                className={`max-w-[80%] rounded-xl p-3 text-base ${
                  message.sender === "ai"
                    ? "rounded-tl-none bg-[var(--color-primary-tint)] text-[var(--color-text-primary)]"
                    : "rounded-tr-none bg-[var(--color-accent-tint)] text-[var(--color-text-primary)]"
                }`}
              >
                {message.text}
              </div>

              {message.sender === "user" && (
                <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-[var(--color-accent-tint)]">
                  <User className="h-4 w-4 text-[var(--color-accent-dark)]" />
                </div>
              )}
            </div>
          ))}

          {isThinking && (
            <div className="flex items-start gap-3">
              <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-[var(--color-primary-tint)]">
                <Bot className="h-4 w-4 text-[var(--color-primary-dark)]" />
              </div>

              <div className="flex gap-1 rounded-xl rounded-tl-none bg-[var(--color-primary-tint)] p-3">
                <span className="h-2 w-2 animate-bounce rounded-full bg-[var(--color-text-secondary)]" />
                <span
                  className="h-2 w-2 animate-bounce rounded-full bg-[var(--color-text-secondary)]"
                  style={{ animationDelay: "0.2s" }}
                />
                <span
                  className="h-2 w-2 animate-bounce rounded-full bg-[var(--color-text-secondary)]"
                  style={{ animationDelay: "0.4s" }}
                />
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {error && (
          <div className="mb-3 rounded-xl border-2 border-[var(--color-danger)] bg-[var(--color-surface)] px-4 py-3 text-sm font-semibold text-[var(--color-danger)]">
            {error}
          </div>
        )}

        <div className="flex gap-3">
          <input
            className="flex-1 rounded-lg border-2 border-[var(--color-border)] bg-[var(--color-bg)] p-4 text-lg text-[var(--color-text-primary)] focus:border-[var(--color-primary)] focus:outline-none"
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
            className="rounded-lg bg-[var(--color-primary-dark)] px-6 py-4 text-lg text-white shadow-lg hover:bg-[var(--color-text-primary)]"
            disabled={isThinking || !input.trim()}
            onClick={handleSend}
          >
            <Send className="h-5 w-5" />
          </Button>
        </div>
      </div>

      <Button
        className="mt-4 rounded-lg bg-[var(--color-primary-dark)] px-10 py-5 text-lg text-white shadow-lg transition-all hover:bg-[var(--color-text-primary)]"
        disabled={isThinking || !canContinue}
        onClick={onNext}
      >
        {isHi ? "अगला: रिपोर्ट अपलोड" : "Next: Upload Reports"}
      </Button>
    </div>
  );
}
