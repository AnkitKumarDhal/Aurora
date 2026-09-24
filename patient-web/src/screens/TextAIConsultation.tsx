import { useEffect, useRef, useState } from "react";
import { flushSync } from "react-dom";
import { Bot, Send, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getInterviewState, type InterviewTurnResult } from "@/api/interview";

interface TextAIConsultationProps {
  draftId: string;
  sessionId: string;
  onNext: () => void;
  onConversationTurn: (
    inputType: "TEXT",
    content: string,
    language: string,
  ) => Promise<InterviewTurnResult | null>;
  language: "en" | "hi";
}

interface Message {
  id: string;
  sender: "ai" | "user";
  text: string;
}

export function TextAIConsultation({
  sessionId,
  onNext,
  onConversationTurn,
  language,
}: TextAIConsultationProps) {
  const isHi = language === "hi";
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [canContinue, setCanContinue] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const hydratedFromDraft = useRef(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isThinking]);

  useEffect(() => {
    if (hydratedFromDraft.current) return;
    hydratedFromDraft.current = true;
    void getInterviewState(sessionId, isHi ? "hi" : "en")
      .then((state) => {
        if (state.next_question)
          setMessages([
            { id: "initial-question", sender: "ai", text: state.next_question },
          ]);
        setCompleted(state.completed);
        setCanContinue(state.completed);
      })
      .catch(() =>
        setError(
          isHi
            ? "इंटरव्यू शुरू नहीं हो सका। कृपया फिर से प्रयास करें।"
            : "The interview could not be started. Please try again.",
        ),
      );
  }, [isHi, sessionId]);

  const handleSend = async () => {
    const content = input.trim();
    if (!content || isThinking || completed) return;
    const localMessageId = `user-${Date.now()}`;
    setError(null);
    flushSync(() => {
      setInput("");
      setCanContinue(false);
      setMessages((previous) => [
        ...previous,
        { id: localMessageId, sender: "user", text: content },
      ]);
      setIsThinking(true);
    });
    await new Promise<void>((resolve) =>
      window.requestAnimationFrame(() => resolve()),
    );
    const result = await onConversationTurn(
      "TEXT",
      content,
      isHi ? "hi" : "en",
    );
    if (!result) {
      setError(
        isHi
          ? "उत्तर भेजने में समस्या हुई। कृपया फिर से प्रयास करें।"
          : "There was a problem sending your response. Please try again.",
      );
      setIsThinking(false);
      return;
    }
    if (result.assistant_response)
      setMessages((previous) => [
        ...previous,
        {
          id: `ai-${result.turn_id}`,
          sender: "ai",
          text: result.assistant_response!,
        },
      ]);
    if (result.completed) {
      setCompleted(true);
      setCanContinue(true);
      if (!result.assistant_response)
        setMessages((previous) => [
          ...previous,
          {
            id: `complete-${result.turn_id}`,
            sender: "ai",
            text: isHi
              ? "धन्यवाद। आप अब अपनी रिपोर्ट अपलोड कर सकते हैं।"
              : "Thank you. You can now proceed to upload your reports.",
          },
        ]);
    }
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
            ? "अपने लक्षण अपने शब्दों में लिखें"
            : "Describe your symptoms naturally"}
        </p>
      </div>
      <div className="flex w-full max-w-3xl flex-1 flex-col overflow-hidden rounded-xl border-2 border-border bg-surface p-4 shadow-sm">
        <div className="mb-4 flex-1 space-y-3 overflow-y-auto pr-2">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex items-start gap-3 ${message.sender === "user" ? "justify-end" : ""}`}
            >
              {message.sender === "ai" && (
                <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-primary-tint">
                  <Bot className="h-4 w-4 text-primary-dark" />
                </div>
              )}
              <div
                className={`max-w-[80%] rounded-xl p-3 text-base ${message.sender === "ai" ? "rounded-tl-none bg-primary-tint text-text-primary" : "rounded-tr-none bg-accent-tint text-text-primary"}`}
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
                <span className="h-2 w-2 animate-bounce rounded-full bg-text-secondary [animation-delay:0.2s]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-text-secondary [animation-delay:0.4s]" />
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
            disabled={isThinking || completed}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") void handleSend();
            }}
            placeholder={
              isHi
                ? "अपने लक्षण यहां लिखें..."
                : "Describe what you are experiencing..."
            }
            value={input}
          />
          <Button
            className="rounded-lg bg-primary-dark px-6 py-4 text-lg text-white shadow-lg hover:bg-text-primary"
            disabled={isThinking || completed || !input.trim()}
            onClick={() => void handleSend()}
          >
            <Send className="h-5 w-5" />
          </Button>
        </div>
      </div>
      <Button
        className="mt-4 rounded-lg bg-primary-dark px-10 py-5 text-lg text-white shadow-lg transition-all hover:bg-text-primary"
        disabled={!canContinue || isThinking}
        onClick={onNext}
      >
        {isHi ? "अगला: रिपोर्ट अपलोड" : "Next: Upload Reports"}
      </Button>
    </div>
  );
}
