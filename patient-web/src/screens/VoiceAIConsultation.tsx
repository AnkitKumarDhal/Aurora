import { useCallback, useEffect, useRef, useState } from "react";
import { flushSync } from "react-dom";
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
  if (error === "aborted") {
    return null;
  }

  if (error === "no-speech") {
    return isHi
      ? "कोई आवाज़ नहीं मिली। कृपया फिर से बोलें।"
      : "No speech was detected. Please try speaking again.";
  }

  if (error === "audio-capture") {
    return isHi
      ? "माइक्रोफोन उपलब्ध नहीं है। कृपया अपनी माइक्रोफोन सेटिंग जांचें।"
      : "The microphone is not available. Please check your microphone settings.";
  }

  if (error === "not-allowed" || error === "service-not-allowed") {
    return isHi
      ? "माइक्रोफोन की अनुमति नहीं मिली। कृपया Chrome में इस साइट के लिए माइक्रोफोन की अनुमति दें।"
      : "Microphone permission was denied. Please allow microphone access for this site in Chrome.";
  }

  if (error === "language-not-supported") {
    return isHi
      ? "चयनित भाषा के लिए वॉयस पहचान उपलब्ध नहीं है।"
      : "Voice recognition is not available for the selected language.";
  }

  if (error === "network") {
    return isHi
      ? "वॉयस पहचान सेवा उपलब्ध नहीं है। कृपया इंटरनेट कनेक्शन जांचें और फिर प्रयास करें।"
      : "The speech recognition service is unavailable. Please check your internet connection and try again.";
  }

  if (error === "MICROPHONE_SECURE_CONTEXT") {
    return isHi
      ? "वॉयस इनपुट के लिए सुरक्षित HTTPS कनेक्शन आवश्यक है।"
      : "Voice input requires a secure HTTPS connection.";
  }

  if (error === "MICROPHONE_UNAVAILABLE") {
    return isHi
      ? "इस ब्राउज़र में माइक्रोफोन इनपुट उपलब्ध नहीं है।"
      : "Microphone input is not available in this browser.";
  }

  if (error === "MICROPHONE_PERMISSION_DENIED") {
    return isHi
      ? "माइक्रोफोन की अनुमति ब्लॉक है। Chrome की साइट सेटिंग में जाकर Microphone को Allow करें।"
      : "Microphone access is blocked. Open Chrome site settings and set Microphone to Allow.";
  }

  if (error === "MICROPHONE_NOT_FOUND") {
    return isHi
      ? "कोई माइक्रोफोन नहीं मिला। कृपया अपने डिवाइस का माइक्रोफोन जांचें।"
      : "No microphone was found. Please check your device microphone.";
  }

  if (error === "MICROPHONE_UNKNOWN_ERROR") {
    return isHi
      ? "माइक्रोफोन शुरू नहीं हो सका। कृपया फिर से प्रयास करें।"
      : "The microphone could not be started. Please try again.";
  }

  return isHi
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

  const [isRequestingMicrophone, setIsRequestingMicrophone] = useState(false);

  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);

  const chatEndRef = useRef<HTMLDivElement>(null);

  const hydrated = useRef(false);

  const recognitionStartingRef = useRef(false);

  const expectedStopRef = useRef(false);

  const latestOnActivityRef = useRef(onActivity);

  const latestHandleUserMessageRef = useRef<(text: string) => Promise<void>>(
    async () => undefined,
  );

  useEffect(() => {
    latestOnActivityRef.current = onActivity;
  }, [onActivity]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, currentTranscript, isSaving]);

  useEffect(() => {
    if (hydrated.current) {
      return;
    }

    hydrated.current = true;

    void getInterviewState(sessionId)
      .then((state) => {
        const nextQuestion = state.next_question;

        if (state.patient_turns > 0 && nextQuestion) {
          setMessages((previous) => [
            ...previous,
            {
              id: "restored-question",
              sender: "ai",
              text: nextQuestion,
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

      flushSync(() => {
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
      });

      await new Promise<void>((resolve) => {
        window.requestAnimationFrame(() => resolve());
      });

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
    [completed, isHi, isSaving, onConversationTurn],
  );

  useEffect(() => {
    latestHandleUserMessageRef.current = handleUserMessage;
  }, [handleUserMessage]);

  useEffect(() => {
    const SpeechRecognition = getSpeechRecognitionConstructor();

    if (!SpeechRecognition) {
      return;
    }

    const recognitionInstance = new SpeechRecognition();

    recognitionInstance.continuous = false;

    recognitionInstance.interimResults = true;

    recognitionInstance.lang = isHi ? "hi-IN" : "en-US";

    recognitionInstance.onstart = () => {
      recognitionStartingRef.current = false;

      expectedStopRef.current = false;

      setIsListening(true);

      latestOnActivityRef.current?.();
    };

    recognitionInstance.onresult = (event: SpeechRecognitionResultEvent) => {
      latestOnActivityRef.current?.();

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
        expectedStopRef.current = true;

        setIsListening(false);

        try {
          recognitionInstance.stop();
        } catch {
          // Recognition may already be ending.
        }

        void latestHandleUserMessageRef.current(finalTranscript.trim());
      }
    };

    recognitionInstance.onerror = (event: SpeechRecognitionErrorEvent) => {
      recognitionStartingRef.current = false;

      setIsListening(false);
      setIsRequestingMicrophone(false);

      if (event.error === "aborted" && expectedStopRef.current) {
        expectedStopRef.current = false;

        return;
      }

      expectedStopRef.current = false;

      const message = getVoiceErrorMessage(event.error, isHi);

      if (message) {
        setError(message);
      }

      console.error("Speech recognition error:", event.error);
    };

    recognitionInstance.onend = () => {
      recognitionStartingRef.current = false;

      setIsListening(false);
      setIsRequestingMicrophone(false);

      if (!expectedStopRef.current) {
        setCurrentTranscript("");
      }

      expectedStopRef.current = false;
    };

    recognitionRef.current = recognitionInstance;

    return () => {
      recognitionStartingRef.current = false;

      expectedStopRef.current = true;

      setIsRequestingMicrophone(false);

      try {
        recognitionInstance.stop();
      } catch {
        // Ignore cleanup errors.
      }

      recognitionRef.current = null;
    };
  }, [isHi]);

  const toggleListening = async () => {
    const currentRecognition = recognitionRef.current;

    if (
      !currentRecognition ||
      isSaving ||
      completed ||
      isRequestingMicrophone
    ) {
      return;
    }

    latestOnActivityRef.current?.();

    if (recognitionStartingRef.current) {
      return;
    }

    if (isListening) {
      expectedStopRef.current = true;

      setIsListening(false);
      setCurrentTranscript("");

      try {
        currentRecognition.stop();
      } catch {
        // Ignore if already stopped.
      }

      return;
    }

    setError(null);
    setCurrentTranscript("");

    recognitionStartingRef.current = true;

    setIsRequestingMicrophone(true);

    try {
      /*
       * This is intentionally triggered
       * from the user's microphone click.
       *
       * On "prompt", mobile Chrome can
       * display its native permission prompt.
       */
      await requestMicrophoneAccess();

      if (recognitionRef.current !== currentRecognition) {
        recognitionStartingRef.current = false;

        setIsRequestingMicrophone(false);

        return;
      }

      expectedStopRef.current = false;

      currentRecognition.start();
    } catch (requestError) {
      recognitionStartingRef.current = false;

      setIsListening(false);

      const errorCode =
        requestError instanceof Error
          ? requestError.message
          : "MICROPHONE_UNKNOWN_ERROR";

      const message = getVoiceErrorMessage(errorCode, isHi);

      setError(
        message ??
          (isHi
            ? "माइक्रोफोन शुरू नहीं हो सका। कृपया फिर से प्रयास करें।"
            : "The microphone could not be started. Please try again."),
      );

      setIsRequestingMicrophone(false);

      console.error("Unable to access microphone:", requestError);
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
                {currentTranscript}
                ...
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
                  style={{
                    animationDelay: "0.2s",
                  }}
                />

                <span
                  className="h-2 w-2 animate-bounce rounded-full bg-text-secondary"
                  style={{
                    animationDelay: "0.4s",
                  }}
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
            disabled={
              !speechRecognitionAvailable ||
              isSaving ||
              completed ||
              isRequestingMicrophone
            }
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
              isListening ? "text-danger" : "text-text-secondary"
            }`}
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
