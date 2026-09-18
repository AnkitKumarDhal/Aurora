import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import {
  Bot,
  User,
  AlertTriangle,
  CheckCircle,
  Clock,
  Mic,
  MicOff,
} from "lucide-react";

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
  const [recognition, setRecognition] = useState<any>(null);
  const [currentTranscript, setCurrentTranscript] = useState("");
  const chatEndRef = useRef<HTMLDivElement>(null);
  const messageCount = useRef(0);

  const aiQuestions = [
    isHi ? "कब से ये लक्षण हैं?" : "How long have you had these symptoms?",
    isHi ? "क्या कोई अन्य लक्षण हैं?" : "Are there any other symptoms?",
    isHi ? "क्या आप कोई दवा ले रहे हैं?" : "Are you taking any medications?",
    isHi
      ? "क्या आपको कोई पुरानी बीमारी है?"
      : "Do you have any chronic illnesses?",
  ];

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });

    if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
      const SpeechRecognition =
        (window as any).SpeechRecognition ||
        (window as any).webkitSpeechRecognition;
      const recognitionInstance = new SpeechRecognition();
      recognitionInstance.continuous = true;
      recognitionInstance.interimResults = true;
      recognitionInstance.lang = isHi ? "hi-IN" : "en-US";

      recognitionInstance.onresult = (event: any) => {
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

      recognitionInstance.onerror = (event: any) => {
        console.error("Speech recognition error:", event.error);
        setIsListening(false);
      };

      recognitionInstance.onend = () => {
        setIsListening(false);
      };

      setRecognition(recognitionInstance);
    }
  }, [isHi]);

  useEffect(() => {
    if (recognition) {
      recognition.lang = isHi ? "hi-IN" : "en-US";
    }
  }, [isHi, recognition]);

  const handleUserMessage = (text: string) => {
    const userMsg: Message = { id: Date.now(), sender: "user", text };
    setMessages((prev) => [...prev, userMsg]);
    messageCount.current += 1;

    const lowerText = text.toLowerCase();
    if (
      lowerText.includes("chest pain") ||
      lowerText.includes("heart") ||
      lowerText.includes("bleeding") ||
      lowerText.includes("can't breathe") ||
      lowerText.includes("severe") ||
      lowerText.includes("छाती") ||
      lowerText.includes("सांस")
    ) {
      setTriageLevel("red");
    } else if (
      lowerText.includes("fever") ||
      lowerText.includes("cough") ||
      lowerText.includes("pain") ||
      lowerText.includes("बुखार") ||
      lowerText.includes("दर्द")
    ) {
      if (triageLevel === "none") setTriageLevel("yellow");
    } else {
      if (triageLevel === "none") setTriageLevel("green");
    }

    setTimeout(() => {
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
  };

  const toggleListening = () => {
    if (isListening) {
      recognition?.stop();
      setIsListening(false);
    } else {
      recognition?.start();
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
    <div className="flex flex-col items-center w-full h-[80vh]">
      {!currentTriage.hidden && (
        <div
          className={`w-full max-w-3xl mb-4 p-3 rounded-lg ${currentTriage.color} text-white flex items-center justify-center gap-3 shadow-lg transition-all duration-500`}
        >
          {currentTriage.icon && <currentTriage.icon className="h-5 w-5" />}
          <span className="text-xl font-bold">{currentTriage.text}</span>
        </div>
      )}

      <div className="text-center mb-4">
        <h2 className="text-2xl font-bold text-[var(--color-text-primary)]">
          {isHi ? "AI वॉयस परामर्श" : "AI Voice Consultation"}
        </h2>
        <p className="text-sm text-[var(--color-text-secondary)]">
          {isHi
            ? "बोलना शुरू करने के लिए माइक बटन दबाएं"
            : "Tap the mic button to start speaking"}
        </p>
      </div>

      <div className="bg-[var(--color-surface)] border-2 border-[var(--color-border)] rounded-xl p-4 w-full max-w-3xl flex-1 flex flex-col overflow-hidden shadow-sm">
        <div className="flex-1 overflow-y-auto space-y-3 pr-2 mb-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex items-start gap-3 ${msg.sender === "user" ? "justify-end" : ""}`}
            >
              {msg.sender === "ai" && (
                <div className="h-8 w-8 rounded-full bg-[var(--color-primary-tint)] flex items-center justify-center flex-shrink-0">
                  <Bot className="h-4 w-4 text-[var(--color-primary-dark)]" />
                </div>
              )}
              <div
                className={`p-3 rounded-xl text-base max-w-[80%] ${msg.sender === "ai" ? "bg-[var(--color-primary-tint)] text-[var(--color-text-primary)] rounded-tl-none" : "bg-[var(--color-accent-tint)] text-[var(--color-text-primary)] rounded-tr-none"}`}
              >
                {msg.text}
              </div>
              {msg.sender === "user" && (
                <div className="h-8 w-8 rounded-full bg-[var(--color-accent-tint)] flex items-center justify-center flex-shrink-0">
                  <User className="h-4 w-4 text-[var(--color-accent-dark)]" />
                </div>
              )}
            </div>
          ))}
          {currentTranscript && (
            <div className="flex items-start gap-3 justify-end">
              <div className="p-3 rounded-xl text-base bg-[var(--color-accent-tint)] text-[var(--color-text-secondary)] rounded-tr-none italic">
                {currentTranscript}...
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        <div className="flex flex-col items-center gap-3">
          <button
            onClick={toggleListening}
            className={`h-16 w-16 rounded-full flex items-center justify-center transition-all ${isListening ? "bg-[var(--color-danger)] animate-pulse" : "bg-[var(--color-primary)] hover:bg-[var(--color-primary-dark)]"}`}
          >
            {isListening ? (
              <MicOff className="h-8 w-8 text-white" />
            ) : (
              <Mic className="h-8 w-8 text-white" />
            )}
          </button>
          <span
            className={`text-sm ${isListening ? "text-[var(--color-danger)]" : "text-[var(--color-text-secondary)]"}`}
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
        onClick={onNext}
        className="mt-4 px-10 py-5 text-lg rounded-lg bg-[var(--color-primary-dark)] hover:bg-[var(--color-text-primary)] text-white transition-all shadow-lg"
      >
        {isHi ? "अगला: रिपोर्ट अपलोड" : "Next: Upload Reports"}
      </Button>
    </div>
  );
}
