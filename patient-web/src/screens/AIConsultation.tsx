import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  AlertTriangle,
  Bot,
  CheckCircle,
  Clock,
  Mic,
  MicOff,
  Send,
  User,
} from "lucide-react";
import {
  getSpeechRecognitionConstructor,
  type SpeechRecognitionInstance,
  type SpeechRecognitionResultEvent,
  type SpeechRecognitionErrorEvent,
} from "@/lib/speechRecognition";

interface AIConsultationProps {
  onNext: () => void;
  language: "en" | "hi";
}

interface Message {
  id: number;
  sender: "ai" | "user";
  text: string;
}

export function AIConsultation({ onNext, language }: AIConsultationProps) {
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
  const [input, setInput] = useState("");
  const [triageLevel, setTriageLevel] = useState<"green" | "yellow" | "red">(
    "green",
  );
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

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

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;

        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        }
      }

      if (finalTranscript) {
        setInput(finalTranscript);
      }
    };

    recognitionInstance.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.error("Speech recognition error:", event.error);
      setIsListening(false);
    };

    recognitionRef.current = recognitionInstance;

    return () => {
      recognitionInstance.stop();
      recognitionRef.current = null;
    };
  }, [isHi]);

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

  const handleSend = () => {
    if (!input.trim()) {
      return;
    }

    const userMsg: Message = {
      id: Date.now(),
      sender: "user",
      text: input,
    };

    setMessages((prev) => [...prev, userMsg]);

    const lowerInput = input.toLowerCase();

    if (
      lowerInput.includes("chest pain") ||
      lowerInput.includes("heart attack") ||
      lowerInput.includes("bleeding") ||
      lowerInput.includes("can't breathe") ||
      lowerInput.includes("severe") ||
      lowerInput.includes("छाती में दर्द") ||
      lowerInput.includes("सांस लेने में कठिनाई")
    ) {
      setTriageLevel("red");
    } else if (
      lowerInput.includes("fever") ||
      lowerInput.includes("cough") ||
      lowerInput.includes("pain") ||
      lowerInput.includes("बुखार") ||
      lowerInput.includes("खांसी")
    ) {
      setTriageLevel("yellow");
    } else {
      setTriageLevel("green");
    }

    setInput("");

    setTimeout(() => {
      const aiResponse: Message = {
        id: Date.now() + 1,
        sender: "ai",
        text: isHi
          ? "मैं समझ गया। क्या आप कुछ और बताना चाहेंगे या अगला चरण चुनें।"
          : "I understand. Would you like to add anything else or select the next step.",
      };

      setMessages((prev) => [...prev, aiResponse]);
    }, 1000);
  };

  const triageConfig = {
    green: {
      color: "bg-success",
      text: isHi ? "नियमित (Routine)" : "Routine",
      icon: CheckCircle,
    },
    yellow: {
      color: "bg-warning",
      text: isHi ? "तत्काल (Urgent)" : "Urgent",
      icon: Clock,
    },
    red: {
      color: "bg-danger animate-pulse",
      text: isHi ? "आपातकालीन (Emergency)" : "EMERGENCY",
      icon: AlertTriangle,
    },
  };

  const currentTriage = triageConfig[triageLevel];

  return (
    <div className="flex h-[80vh] w-full flex-col items-center py-4">
      <div
        className={`mb-4 flex w-full max-w-4xl items-center justify-center gap-3 rounded-lg p-3 text-white shadow-lg transition-all duration-500 ${currentTriage.color}`}
      >
        <currentTriage.icon className="h-5 w-5" />
        <span className="text-xl font-bold">{currentTriage.text}</span>
      </div>

      <div className="mb-4 space-y-1 text-center">
        <h2 className="text-2xl font-bold text-text-primary">
          {isHi ? "AI परामर्श" : "AI Consultation"}
        </h2>
      </div>

      <div className="flex w-full max-w-4xl flex-1 flex-col overflow-hidden rounded-xl border-2 border-border bg-surface p-4 shadow-sm">
        <div className="mb-4 flex-1 space-y-3 overflow-y-auto pr-2">
          {messages.map((msg) => (
            <div
              className={`flex items-start gap-3 ${msg.sender === "user" ? "justify-end" : ""}`}
              key={msg.id}
            >
              {msg.sender === "ai" && (
                <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-primary-tint">
                  <Bot className="h-4 w-4 text-primary-dark" />
                </div>
              )}

              <div
                className={`max-w-[75%] rounded-xl p-3 text-base ${
                  msg.sender === "ai"
                    ? "rounded-tl-none bg-primary-tint text-text-primary"
                    : "rounded-tr-none bg-accent-tint text-text-primary"
                }`}
              >
                {msg.text}
              </div>

              {msg.sender === "user" && (
                <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-accent-tint">
                  <User className="h-4 w-4 text-accent-dark" />
                </div>
              )}
            </div>
          ))}

          <div ref={chatEndRef} />
        </div>

        <div className="flex gap-3">
          <Button
            type="button"
            variant="outline"
            className={`rounded-lg border-2 p-4 transition-all active:scale-[0.95] ${
              isListening
                ? "border-danger bg-danger text-white hover:bg-danger/90 hover:text-white"
                : "border-border bg-surface text-text-secondary hover:border-primary hover:bg-primary-tint"
            }`}
            onClick={toggleListening}
          >
            {isListening ? (
              <MicOff className="h-5 w-5" />
            ) : (
              <Mic className="h-5 w-5" />
            )}
          </Button>

          <input
            className="flex-1 rounded-lg border-2 border-border bg-bg p-4 text-lg text-text-primary focus:border-primary focus:outline-none"
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                handleSend();
              }
            }}
            placeholder={
              isHi
                ? "अपने लक्षण यहां टाइप करें या बोलें..."
                : "Type or speak your symptoms..."
            }
            value={input}
          />

          <Button
            type="button"
            className="rounded-lg bg-primary-dark px-6 py-4 text-lg text-white shadow-lg transition-all hover:bg-text-primary active:scale-[0.98]"
            onClick={handleSend}
          >
            <Send className="h-5 w-5" />
          </Button>
        </div>

        {isListening && (
          <div className="mt-2 flex items-center gap-2 text-sm text-primary">
            <div className="flex gap-1">
              <span className="h-4 w-1 rounded-full bg-primary animate-pulse" />
              <span
                className="h-4 w-1 rounded-full bg-primary animate-pulse"
                style={{ animationDelay: "0.1s" }}
              />
              <span
                className="h-4 w-1 rounded-full bg-primary animate-pulse"
                style={{ animationDelay: "0.2s" }}
              />
            </div>
            {isHi ? "सुन रहा है..." : "Listening..."}
          </div>
        )}
      </div>

      <Button
        type="button"
        className="mt-4 min-w-[250px] rounded-lg bg-primary-dark px-10 py-5 text-lg text-white shadow-lg transition-all hover:bg-text-primary active:scale-[0.98]"
        onClick={onNext}
      >
        {isHi ? "अगला: रिपोर्ट अपलोड करें" : "Next: Upload Reports"}
      </Button>
    </div>
  );
}
