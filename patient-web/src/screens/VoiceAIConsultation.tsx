import { useCallback, useEffect, useRef, useState } from "react";
import { Bot, Mic, MicOff, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getInterviewState, type InterviewTurnResult } from "@/api/interview";
import {
  getSpeechRecognitionConstructor,
  type SpeechRecognitionErrorEvent,
  type SpeechRecognitionInstance,
  type SpeechRecognitionResultEvent,
} from "@/lib/speechRecognition";

interface VoiceAIConsultationProps {
  draftId: string;
  sessionId: string;
  onNext: () => void;
  onConversationTurn: (
    inputType: "AUDIO",
    content: string,
    language: string,
  ) => Promise<InterviewTurnResult | null>;
  onActivity?: () => void;
  language: "en" | "hi";
}

interface Message {
  id: string;
  sender: "ai" | "user";
  text: string;
}

export function VoiceAIConsultation({
  sessionId,
  onNext,
  onConversationTurn,
  onActivity,
  language,
}: VoiceAIConsultationProps) {
  const isHi = language === "hi";
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "initial",
      sender: "ai",
      text: isHi
        ? "नमस्ते! मैं औरोरा AI हूं। कृपया अपने लक्षण बताएं।"
        : "Hello! I am Aurora AI. Please describe your symptoms.",
    },
  ]);
  const [isListening, setIsListening] = useState(false);
  const [currentTranscript, setCurrentTranscript] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [canContinue, setCanContinue] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const hydrated = useRef(false);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, currentTranscript, isSaving]);

  useEffect(() => {
    if (hydrated.current) {
      return;
    }

    hydrated.current = true;

    void getInterviewState(sessionId)
      .then((state) => {
        if (state.patient_turns > 0 && state.next_question) {
          setMessages((previous) => [
            ...previous,
            {
              id: "restored-question",
              sender: "ai",
              text: state.next_question,
            },
          ]);
        }

        setCompleted(state.completed);

        if (state.patient_turns > 0) {
          setCanContinue(true);
        }
      })
      .catch(() => undefined);
  }, [sessionId]);

  const handleUserMessage = useCallback(
    async (text: string) => {
      const content = text.trim();

      if (!content || isSaving || completed) {
        return;
      }

      const localMessageId = `user-${Date.now()}`;

      onActivity?.();
      setError(null);
      setCanContinue(true);
      setMessages((previous) => [
        ...previous,
        {
          id: localMessageId,
          sender: "user",
          text: content,
        },
      ]);
      setCurrentTranscript("");
      setIsSaving(true);

      const result = await onConversationTurn(
        "AUDIO",
        content,
        isHi ? "hi" : "en",
      );

      if (!result) {
        setError(
          isHi
            ? "उत्तर भेजने में समस्या हुई। कृपया फिर से प्रयास करें।"
            : "There was a problem sending your response. Please try again.",
        );
        setIsSaving(false);
        return;
      }

      if (result.assistant_response) {
        setMessages((previous) => [
          ...previous,
          {
            id: `ai-${result.turn_id}`,
            sender: "ai",
            text: result.assistant_response!,
          },
        ]);
      }

      if (result.completed) {
        setCompleted(true);

        if (!result.assistant_response) {
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
      }

      setIsSaving(false);
    },
    [completed, isHi, isSaving, onActivity, onConversationTurn],
  );

  useEffect(() => {
    const SpeechRecognition = getSpeechRecognitionConstructor();

    if (!SpeechRecognition) {
      return;
    }

    const recognitionInstance = new SpeechRecognition();

    recognitionInstance.continuous = true;
    recognitionInstance.interimResults = true;
    recognitionInstance.lang = isHi ? "hi-IN" : "en-US";

    recognitionInstance.onstart = () => {
      onActivity?.();
    };

    recognitionInstance.onresult = (event: SpeechRecognitionResultEvent) => {
      onActivity?.();

      let finalTranscript = "";
      let interimTranscript = "";

      for (
        let index = event.resultIndex;
        index < event.results.length;
        index += 1
      ) {
        const transcript = event.results[index][0].transcript;

        if (event.results[index].isFinal) {
          finalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }

      setCurrentTranscript(interimTranscript);

      if (finalTranscript.trim()) {
        void handleUserMessage(finalTranscript);
      }
    };

    recognitionInstance.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.error("Speech recognition error:", event.error);
      setIsListening(false);
      setError(
        isHi
          ? "वॉयस इनपुट में समस्या हुई। कृपया फिर से प्रयास करें।"
          : "There was a problem with voice input. Please try again.",
      );
    };

    recognitionInstance.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognitionInstance;

    return () => {
      recognitionInstance.stop();
      recognitionRef.current = null;
    };
  }, [handleUserMessage, isHi, onActivity]);

  const toggleListening = () => {
    const currentRecognition = recognitionRef.current;

    if (!currentRecognition || isSaving || completed) {
      return;
    }

    onActivity?.();

    if (isListening) {
      currentRecognition.stop();
      setIsListening(false);
      return;
    }

    setError(null);
    currentRecognition.start();
    setIsListening(true);
  };

  return (
    <div className="flex h-[80vh] w-full flex-col items-center">
      <div className="mb-4 text-center">
        <h2 className="text-2xl font-bold text-text-primary">
          {isHi ? "AI वॉयस परामर्श" : "AI Voice Consultation"}
        </h2>

        <p className="text-sm text-text-secondary">
          {isHi
            ? "बोलना शुरू करने के लिए माइक बटन दबाएं"
            : "Tap the mic button to start speaking"}
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

          {currentTranscript && (
            <div className="flex items-start justify-end gap-3">
              <div className="max-w-[80%] rounded-xl rounded-tr-none bg-accent-tint p-3 text-base italic text-text-secondary">
                {currentTranscript}...
              </div>
            </div>
          )}

          {isSaving && (
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

        <div className="flex flex-col items-center gap-3">
          <button
            className={`flex h-16 w-16 items-center justify-center rounded-full transition-all ${
              isListening
                ? "animate-pulse bg-danger"
                : "bg-primary hover:bg-primary-dark"
            }`}
            disabled={isSaving || completed}
            onClick={toggleListening}
            type="button"
          >
            {isListening ? (
              <MicOff className="h-8 w-8 text-white" />
            ) : (
              <Mic className="h-8 w-8 text-white" />
            )}
          </button>

          <span
            className={`text-sm ${isListening ? "text-danger" : "text-text-secondary"}`}
          >
            {isListening
              ? isHi
                ? "सुन रहा है..."
                : "Listening..."
              : isHi
                ? "बोलने के लिए टैप करें"
                : "Tap to speak"}
          </span>
        </div>
      </div>

      <Button
        className="mt-4 rounded-lg bg-primary-dark px-10 py-5 text-lg text-white shadow-lg transition-all hover:bg-text-primary"
        disabled={isListening || isSaving || !canContinue}
        onClick={onNext}
      >
        {isHi ? "अगला: रिपोर्ट अपलोड" : "Next: Upload Reports"}
      </Button>
    </div>
  );
}
