import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  AlertTriangle,
  Bot,
  CheckCircle,
  Clock,
  Mic,
  MicOff,
  User,
} from "lucide-react";
import {
  getSpeechRecognitionConstructor,
  type SpeechRecognitionErrorEvent,
  type SpeechRecognitionInstance,
  type SpeechRecognitionResultEvent,
} from "@/lib/speechRecognition";

interface VoiceAIConsultationProps {
  onNext: () => void;
  language: "en" | "hi";
}

interface Message {
  id: number;
  sender: "ai" | "user";
  text: string;
}

export function VoiceAIConsultation({
  onNext,
  language,
}: VoiceAIConsultationProps) {
  const isHi = language === "hi";
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      sender: "ai",
      text: isHi
        ? "नमस्ते! मैं औरोरा AI हूं। कृपया अपने लक्षण बताएं।"
        : "Hello! I am Aurora AI. Please describe your symptoms.",
    },
  ]);
  const [triageLevel, setTriageLevel] = useState<
    "none" | "green" | "yellow" | "red"
  >("none");
  const [isListening, setIsListening] = useState(false);
  const [currentTranscript, setCurrentTranscript] = useState("");
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const messageCount = useRef(0);

  const handleUserMessage = useCallback(
    (text: string) => {
      const userMsg: Message = {
        id: Date.now(),
        sender: "user",
        text,
      };

      setMessages((prev) => [...prev, userMsg]);
      messageCount.current += 1;

      const lowerText = text.toLowerCase();

      const isRed =
        lowerText.includes("chest pain") ||
        lowerText.includes("heart") ||
        lowerText.includes("bleeding") ||
        lowerText.includes("can't breathe") ||
        lowerText.includes("severe") ||
        lowerText.includes("छाती") ||
        lowerText.includes("सांस");

      const isYellow =
        lowerText.includes("fever") ||
        lowerText.includes("cough") ||
        lowerText.includes("pain") ||
        lowerText.includes("बुखार") ||
        lowerText.includes("दर्द");

      setTriageLevel((currentLevel) => {
        if (isRed) {
          return "red";
        }

        if (isYellow && currentLevel === "none") {
          return "yellow";
        }

        if (!isYellow && currentLevel === "none") {
          return "green";
        }

        return currentLevel;
      });

      setTimeout(() => {
        const aiQuestions = [
          isHi ? "कब से ये लक्षण हैं?" : "How long have you had these symptoms?",
          isHi ? "क्या कोई अन्य लक्षण हैं?" : "Are there any other symptoms?",
          isHi ? "क्या आप कोई दवा ले रहे हैं?" : "Are you taking any medications?",
          isHi
            ? "क्या आपको कोई पुरानी बीमारी है?"
            : "Do you have any chronic illnesses?",
        ];

        const questionIndex = Math.min(
          messageCount.current - 1,
          aiQuestions.length - 1,
        );

        const aiResponse: Message = {
          id: Date.now() + 1,
          sender: "ai",
          text: aiQuestions[questionIndex],
        };

        setMessages((prev) => [...prev, aiResponse]);
      }, 1500);
    },
    [isHi],
  );

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    const SpeechRecognition = getSpeechRecognitionConstructor();

    if (!SpeechRecognition) {
      return;
    }

    const recognitionInstance = new SpeechRecognition();

    recognitionInstance.continuous = true;
    recognitionInstance.interimResults = true;
    recognitionInstance.lang = isHi ? "hi-IN" : "en-US";

    recognitionInstance.onresult = (event: SpeechRecognitionResultEvent) => {
      let finalTranscript = "";
      let interimTranscript = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;

        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }

      setCurrentTranscript(interimTranscript);

      if (finalTranscript) {
        handleUserMessage(finalTranscript);
        setCurrentTranscript("");
      }
    };

    recognitionInstance.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.error("Speech recognition error:", event.error);
      setIsListening(false);
    };

    recognitionInstance.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognitionInstance;

    return () => {
      recognitionInstance.stop();
      recognitionRef.current = null;
    };
  }, [handleUserMessage, isHi]);

  const toggleListening = () => {
    const currentRecognition = recognitionRef.current;

    if (isListening) {
      currentRecognition?.stop();
      setIsListening(false);
    } else {
      if (!currentRecognition) {
        return;
      }

      currentRecognition.start();
      setIsListening(true);
    }
  };

  const triageConfig = {
    none: {
      color: "bg-gray-300",
      text: isHi ? "विश्लेषण..." : "Analyzing...",
      icon: null,
      hidden: true,
    },
    green: {
      color: "bg-[var(--color-success)]",
      text: isHi ? "नियमित (Routine)" : "Routine",
      icon: CheckCircle,
      hidden: false,
    },
    yellow: {
      color: "bg-[var(--color-warning)]",
      text: isHi ? "तत्काल (Urgent)" : "Urgent",
      icon: Clock,
      hidden: false,
    },
    red: {
      color: "bg-[var(--color-danger)] animate-pulse",
      text: isHi ? "आपातकालीन (Emergency)" : "🚨 EMERGENCY",
      icon: AlertTriangle,
      hidden: false,
    },
  };

  const currentTriage = triageConfig[triageLevel];

  return (
    <div className="flex h-[80vh] w-full flex-col items-center">
      {!currentTriage.hidden && (
        <div
          className={`mb-4 flex w-full max-w-3xl items-center justify-center gap-3 rounded-lg p-3 text-white shadow-lg transition-all duration-500 ${currentTriage.color}`}
        >
          {currentTriage.icon && <currentTriage.icon className="h-5 w-5" />}
          <span className="text-xl font-bold">{currentTriage.text}</span>
        </div>
      )}

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
          {messages.map((msg) => (
            <div
              className={`flex items-start gap-3 ${
                msg.sender === "user" ? "justify-end" : ""
              }`}
              key={msg.id}
            >
              {msg.sender === "ai" && (
                <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-[var(--color-primary-tint)]">
                  <Bot className="h-4 w-4 text-[var(--color-primary-dark)]" />
                </div>
              )}

              <div
                className={`max-w-[80%] rounded-xl p-3 text-base ${
                  msg.sender === "ai"
                    ? "rounded-tl-none bg-[var(--color-primary-tint)] text-[var(--color-text-primary)]"
                    : "rounded-tr-none bg-[var(--color-accent-tint)] text-[var(--color-text-primary)]"
                }`}
              >
                {msg.text}
              </div>

              {msg.sender === "user" && (
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

          <div ref={chatEndRef} />
        </div>

        <div className="flex flex-col items-center gap-3">
          <button
            className={`flex h-16 w-16 items-center justify-center rounded-full transition-all ${
              isListening
                ? "animate-pulse bg-[var(--color-danger)]"
                : "bg-[var(--color-primary)] hover:bg-[var(--color-primary-dark)]"
            }`}
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
        onClick={onNext}
      >
        {isHi ? "अगला: रिपोर्ट अपलोड" : "Next: Upload Reports"}
      </Button>
    </div>
  );
}
