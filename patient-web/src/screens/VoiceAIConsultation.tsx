import { useCallback, useEffect, useRef, useState } from "react";
import { Bot, Mic, MicOff, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { loadPatientDraft } from "@/lib/patientDraft";
import {
  getSpeechRecognitionConstructor,
  type SpeechRecognitionErrorEvent,
  type SpeechRecognitionInstance,
  type SpeechRecognitionResultEvent,
} from "@/lib/speechRecognition";

interface VoiceAIConsultationProps {
  draftId: string;
  onNext: () => void;
  onConversationTurn: (
    inputType: "AUDIO",
    content: string,
    language: string,
  ) => boolean;
  onActivity?: () => void;
  language: "en" | "hi";
}

interface Message {
  id: string;
  sender: "ai" | "user";
  text: string;
}

interface InitialVoiceState {
  messages: Message[];
  existingTurnCount: number;
}

function getInitialVoiceState(
  draftId: string,
  isHi: boolean,
): InitialVoiceState {
  const initialMessage: Message = {
    id: "initial",
    sender: "ai",
    text: isHi
      ? "नमस्ते! मैं औरोरा AI हूं। कृपया अपने लक्षण बताएं।"
      : "Hello! I am Aurora AI. Please describe your symptoms.",
  };

  const draft = loadPatientDraft();

  if (!draft || draft.draft_id !== draftId) {
    return {
      messages: [initialMessage],
      existingTurnCount: 0,
    };
  }

  const existingTurns = draft.conversation_turns.filter(
    (turn) => turn.input_type === "AUDIO",
  );

  if (existingTurns.length === 0) {
    return {
      messages: [initialMessage],
      existingTurnCount: 0,
    };
  }

  return {
    messages: [
      initialMessage,
      ...existingTurns.map((turn) => ({
        id: turn.local_id,
        sender: "user" as const,
        text: turn.content,
      })),
    ],
    existingTurnCount: existingTurns.length,
  };
}

export function VoiceAIConsultation({
  draftId,
  onNext,
  onConversationTurn,
  onActivity,
  language,
}: VoiceAIConsultationProps) {
  const isHi = language === "hi";
  const [initialState] = useState<InitialVoiceState>(() =>
    getInitialVoiceState(draftId, isHi),
  );

  const [messages, setMessages] = useState<Message[]>(initialState.messages);
  const [isListening, setIsListening] = useState(false);
  const [currentTranscript, setCurrentTranscript] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [canContinue, setCanContinue] = useState(
    initialState.existingTurnCount > 0,
  );
  const [error, setError] = useState<string | null>(null);

  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const messageCount = useRef(initialState.existingTurnCount);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, currentTranscript, isSaving]);

  const handleUserMessage = useCallback(
    (text: string) => {
      const content = text.trim();

      if (!content || isSaving) {
        return;
      }

      onActivity?.();
      setError(null);
      setIsSaving(true);

      const saved = onConversationTurn("AUDIO", content, isHi ? "hi" : "en");

      if (!saved) {
        setError("Unable to save your response locally.");
        setIsSaving(false);
        return;
      }

      messageCount.current += 1;

      setMessages((previous) => [
        ...previous,
        {
          id: `voice-user-${messageCount.current}`,
          sender: "user",
          text: content,
        },
      ]);

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
            id: `voice-ai-${messageCount.current}`,
            sender: "ai",
            text: questions[questionIndex],
          },
        ]);

        setIsSaving(false);
      }, 1500);
    },
    [isHi, isSaving, onActivity, onConversationTurn],
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
        handleUserMessage(finalTranscript);
        setCurrentTranscript("");
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

    if (!currentRecognition || isSaving) {
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
        <h2 className="text-2xl font-bold text-[var(--color-text-primary)]">
          {isHi ? "AI वॉयस परामर्श" : "AI Voice Consultation"}
        </h2>

        <p className="text-sm text-[var(--color-text-secondary)]">
          {isHi
            ? "बोलना शुरू करने के लिए माइक बटन दबाएं"
            : "Tap the mic button to start speaking"}
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

          {currentTranscript && (
            <div className="flex items-start justify-end gap-3">
              <div className="max-w-[80%] rounded-xl rounded-tr-none bg-[var(--color-accent-tint)] p-3 text-base italic text-[var(--color-text-secondary)]">
                {currentTranscript}...
              </div>
            </div>
          )}

          {isSaving && (
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

        <div className="flex flex-col items-center gap-3">
          <button
            className={`flex h-16 w-16 items-center justify-center rounded-full transition-all ${
              isListening
                ? "animate-pulse bg-[var(--color-danger)]"
                : "bg-[var(--color-primary)] hover:bg-[var(--color-primary-dark)]"
            }`}
            disabled={isSaving}
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
            className={`text-sm ${
              isListening
                ? "text-[var(--color-danger)]"
                : "text-[var(--color-text-secondary)]"
            }`}
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
        className="mt-4 rounded-lg bg-[var(--color-primary-dark)] px-10 py-5 text-lg text-white shadow-lg transition-all hover:bg-[var(--color-text-primary)]"
        disabled={isListening || isSaving || !canContinue}
        onClick={onNext}
      >
        {isHi ? "अगला: रिपोर्ट अपलोड" : "Next: Upload Reports"}
      </Button>
    </div>
  );
}
