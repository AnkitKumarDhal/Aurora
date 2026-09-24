import { useCallback, useEffect, useRef, useState } from "react";
import { Bot, Mic, MicOff, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getInterviewState, type InterviewTurnResult } from "@/api/interview";
import {
  getSpeechRecognitionConstructor,
  requestMicrophoneAccess,
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

function getVoiceErrorMessage(error: string, isHi: boolean): string | null {
  if (error === "aborted") return null;
  const messages: Record<string, [string, string]> = {
    "no-speech": [
      "No speech was detected. Please try speaking again.",
      "कोई आवाज़ नहीं मिली। कृपया फिर से बोलें।",
    ],
    "audio-capture": [
      "The microphone is not available. Please check your microphone settings.",
      "माइक्रोफोन उपलब्ध नहीं है। कृपया अपनी माइक्रोफोन सेटिंग जांचें।",
    ],
    "not-allowed": [
      "Microphone permission was denied. Please allow microphone access for this site.",
      "माइक्रोफोन की अनुमति नहीं मिली। कृपया इस साइट के लिए माइक्रोफोन की अनुमति दें।",
    ],
    "service-not-allowed": [
      "Microphone permission was denied. Please allow microphone access for this site.",
      "माइक्रोफोन की अनुमति नहीं मिली। कृपया इस साइट के लिए माइक्रोफोन की अनुमति दें।",
    ],
    "language-not-supported": [
      "Voice recognition is not available for the selected language.",
      "चयनित भाषा के लिए वॉयस पहचान उपलब्ध नहीं है।",
    ],
    network: [
      "The speech recognition service is unavailable. Please try again.",
      "वॉयस पहचान सेवा उपलब्ध नहीं है। कृपया फिर से प्रयास करें।",
    ],
    MICROPHONE_SECURE_CONTEXT: [
      "Voice input requires a secure HTTPS connection.",
      "वॉयस इनपुट के लिए सुरक्षित HTTPS कनेक्शन आवश्यक है।",
    ],
    MICROPHONE_UNAVAILABLE: [
      "Microphone input is not available in this browser.",
      "इस ब्राउज़र में माइक्रोफोन इनपुट उपलब्ध नहीं है।",
    ],
    MICROPHONE_PERMISSION_DENIED: [
      "Microphone access is blocked. Allow microphone access in site settings.",
      "माइक्रोफोन की अनुमति ब्लॉक है। साइट सेटिंग में Microphone को Allow करें।",
    ],
    MICROPHONE_NOT_FOUND: [
      "No microphone was found. Please check your device microphone.",
      "कोई माइक्रोफोन नहीं मिला। कृपया अपने डिवाइस का माइक्रोफोन जांचें।",
    ],
    MICROPHONE_UNKNOWN_ERROR: [
      "The microphone could not be started. Please try again.",
      "माइक्रोफोन शुरू नहीं हो सका। कृपया फिर से प्रयास करें।",
    ],
  };
  const pair = messages[error];
  return pair
    ? isHi
      ? pair[1]
      : pair[0]
    : isHi
      ? "वॉयस इनपुट में समस्या हुई। कृपया फिर से प्रयास करें।"
      : "There was a problem with voice input. Please try again.";
}

export function VoiceAIConsultation({
  sessionId,
  onNext,
  onConversationTurn,
  onActivity,
  language,
}: VoiceAIConsultationProps) {
  const isHi = language === "hi";
  const [messages, setMessages] = useState<Message[]>([]);
  const [isListening, setIsListening] = useState(false);
  const [currentTranscript, setCurrentTranscript] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [canContinue, setCanContinue] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isRequestingMicrophone, setIsRequestingMicrophone] = useState(false);
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const hydrated = useRef(false);
  const starting = useRef(false);
  const expectedStop = useRef(false);
  const latestOnActivity = useRef(onActivity);
  const latestHandler = useRef<(text: string) => Promise<void>>(
    async () => undefined,
  );

  useEffect(() => {
    latestOnActivity.current = onActivity;
  }, [onActivity]);
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, currentTranscript, isSaving]);

  useEffect(() => {
    if (hydrated.current) return;
    hydrated.current = true;
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

  const handleUserMessage = useCallback(
    async (text: string) => {
      const content = text.trim();
      if (!content || isSaving || completed) return;
      setError(null);
      setCanContinue(false);
      setCurrentTranscript("");
      setMessages((previous) => [
        ...previous,
        { id: `user-${Date.now()}`, sender: "user", text: content },
      ]);
      setIsSaving(true);
      latestOnActivity.current?.();
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
        const questionKey = result.assistant_response
          .trim()
          .toLowerCase()
          .replace(/[^a-z0-9\u0900-\u097f]+/gi, " ")
          .replace(/\\s+/g, " ")
          .trim();

        setMessages((previous) => {
          const alreadyShown = previous.some(
            (message) =>
              message.sender === "ai" &&
              message.text
                .trim()
                .toLowerCase()
                .replace(/[^a-z0-9\u0900-\u097f]+/gi, " ")
                .replace(/\\s+/g, " ")
                .trim() === questionKey,
          );

          if (alreadyShown) return previous;

          return [
            ...previous,
            {
              id: `ai-${result.turn_id}`,
              sender: "ai",
              text: result.assistant_response!,
            },
          ];
        });
      }
      if (result.completed) {
        setCompleted(true);
        setCanContinue(true);
      }
      setIsSaving(false);
    },
    [completed, isHi, isSaving, onConversationTurn],
  );

  useEffect(() => {
    latestHandler.current = handleUserMessage;
  }, [handleUserMessage]);

  useEffect(() => {
    const SpeechRecognition = getSpeechRecognitionConstructor();
    if (!SpeechRecognition) return;
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = isHi ? "hi-IN" : "en-US";
    recognition.onstart = () => {
      starting.current = false;
      expectedStop.current = false;
      setIsListening(true);
      setIsRequestingMicrophone(false);
      latestOnActivity.current?.();
    };
    recognition.onresult = (event: SpeechRecognitionResultEvent) => {
      latestOnActivity.current?.();
      let finalText = "";
      let interimText = "";
      for (
        let index = event.resultIndex;
        index < event.results.length;
        index += 1
      ) {
        const value = event.results[index][0].transcript;
        if (event.results[index].isFinal) finalText += value;
        else interimText += value;
      }
      setCurrentTranscript(interimText);
      if (finalText.trim()) {
        expectedStop.current = true;
        setIsListening(false);
        try {
          recognition.stop();
        } catch {}
        void latestHandler.current(finalText);
      }
    };
    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      starting.current = false;
      setIsListening(false);
      setIsRequestingMicrophone(false);
      if (event.error === "aborted" && expectedStop.current) {
        expectedStop.current = false;
        return;
      }
      expectedStop.current = false;
      const message = getVoiceErrorMessage(event.error, isHi);
      if (message) setError(message);
    };
    recognition.onend = () => {
      starting.current = false;
      setIsListening(false);
      setIsRequestingMicrophone(false);
      if (!expectedStop.current) setCurrentTranscript("");
      expectedStop.current = false;
    };
    recognitionRef.current = recognition;
    return () => {
      expectedStop.current = true;
      try {
        recognition.stop();
      } catch {}
      recognitionRef.current = null;
    };
  }, [isHi]);

  const toggleListening = async () => {
    const recognition = recognitionRef.current;
    if (
      !recognition ||
      isSaving ||
      completed ||
      isRequestingMicrophone ||
      starting.current
    )
      return;
    latestOnActivity.current?.();
    if (isListening) {
      expectedStop.current = true;
      setIsListening(false);
      setCurrentTranscript("");
      try {
        recognition.stop();
      } catch {}
      return;
    }
    setError(null);
    setCurrentTranscript("");
    starting.current = true;
    setIsRequestingMicrophone(true);
    try {
      await requestMicrophoneAccess();
      if (recognitionRef.current !== recognition) return;
      expectedStop.current = false;
      recognition.start();
    } catch (requestError) {
      starting.current = false;
      setIsRequestingMicrophone(false);
      const code =
        requestError instanceof Error
          ? requestError.message
          : "MICROPHONE_UNKNOWN_ERROR";
      const message = getVoiceErrorMessage(code, isHi);
      setError(
        message ??
          (isHi
            ? "माइक्रोफोन शुरू नहीं हो सका।"
            : "The microphone could not be started."),
      );
    }
  };

  const speechRecognitionAvailable = getSpeechRecognitionConstructor() !== null;

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
        <div className="flex flex-col items-center gap-3">
          <button
            className={`flex h-16 w-16 items-center justify-center rounded-full transition-all ${isListening ? "animate-pulse bg-danger" : "bg-primary hover:bg-primary-dark"}`}
            disabled={
              !speechRecognitionAvailable ||
              isSaving ||
              completed ||
              isRequestingMicrophone
            }
            onClick={() => void toggleListening()}
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
            {!speechRecognitionAvailable
              ? isHi
                ? "वॉयस इनपुट उपलब्ध नहीं है"
                : "Voice input unavailable"
              : isRequestingMicrophone
                ? isHi
                  ? "माइक्रोफोन की अनुमति मांगी जा रही है..."
                  : "Requesting microphone access..."
                : isListening
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
