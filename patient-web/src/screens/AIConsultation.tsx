import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Bot, User, Send, AlertTriangle, CheckCircle, Clock, Mic, MicOff } from 'lucide-react';

interface AIConsultationProps {
  onNext: () => void;
  language: 'en' | 'hi';
}

interface Message {
  id: number;
  sender: 'ai' | 'user';
  text: string;
}

export function AIConsultation({ onNext, language }: AIConsultationProps) {
  const isHi = language === 'hi';
  const [messages, setMessages] = useState<Message[]>([
    { id: 1, sender: 'ai', text: isHi ? 'नमस्ते! मैं औरोरा AI हूं। कृपया अपने लक्षण बताएं।' : 'Hello! I am Aurora AI. Please describe your symptoms.' }
  ]);
  const [input, setInput] = useState('');
  const [triageLevel, setTriageLevel] = useState<'green' | 'yellow' | 'red'>('green');
  const [isListening, setIsListening] = useState(false);
  const [recognition, setRecognition] = useState<any>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    
    // Initialize Speech Recognition
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      const recognitionInstance = new SpeechRecognition();
      recognitionInstance.continuous = true;
      recognitionInstance.interimResults = true;
      recognitionInstance.lang = isHi ? 'hi-IN' : 'en-US';

      recognitionInstance.onresult = (event: any) => {
        let finalTranscript = '';

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

      recognitionInstance.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
      };

      setRecognition(recognitionInstance);
    }
  }, [isHi]);

  useEffect(() => {
    if (recognition) {
      recognition.lang = isHi ? 'hi-IN' : 'en-US';
    }
  }, [isHi, recognition]);

  const toggleListening = () => {
    if (isListening) {
      recognition?.stop();
      setIsListening(false);
    } else {
      recognition?.start();
      setIsListening(true);
    }
  };

  const handleSend = () => {
    if (!input.trim()) return;

    const userMsg: Message = { id: Date.now(), sender: 'user', text: input };
    setMessages(prev => [...prev, userMsg]);
    
    const lowerInput = input.toLowerCase();
    
    // Triage Logic
    if (lowerInput.includes('chest pain') || lowerInput.includes('heart attack') || lowerInput.includes('bleeding') || lowerInput.includes('can\'t breathe') || lowerInput.includes('severe') || lowerInput.includes('छाती में दर्द') || lowerInput.includes('सांस लेने में कठिनाई')) {
      setTriageLevel('red');
    } else if (lowerInput.includes('fever') || lowerInput.includes('cough') || lowerInput.includes('pain') || lowerInput.includes('बुखार') || lowerInput.includes('खांसी')) {
      setTriageLevel('yellow');
    } else {
      setTriageLevel('green');
    }

    setInput('');

    // Simulate AI Response
    setTimeout(() => {
      const aiResponse: Message = { 
        id: Date.now() + 1, 
        sender: 'ai', 
        text: isHi 
          ? 'मैं समझ गया। क्या आप कुछ और बताना चाहेंगे या अगला चरण चुनें।' 
          : 'I understand. Would you like to add anything else or select the next step.' 
      };
      setMessages(prev => [...prev, aiResponse]);
    }, 1000);
  };

  const triageConfig = {
    green: { color: 'bg-[var(--color-success)]', text: isHi ? 'नियमित (Routine)' : 'Routine', icon: CheckCircle },
    yellow: { color: 'bg-[var(--color-warning)]', text: isHi ? 'तत्काल (Urgent)' : 'Urgent', icon: Clock },
    red: { color: 'bg-[var(--color-danger)] animate-pulse', text: isHi ? 'आपातकालीन (Emergency)' : 'EMERGENCY', icon: AlertTriangle },
  };

  const currentTriage = triageConfig[triageLevel];

  return (
    <div className="flex flex-col items-center w-full h-[80vh] py-4">
      {/* Triage Badge */}
      <div className={`w-full max-w-4xl mb-4 p-3 rounded-lg ${currentTriage.color} text-white flex items-center justify-center gap-3 shadow-lg transition-all duration-500`}>
        <currentTriage.icon className="h-5 w-5" />
        <span className="text-xl font-bold">{currentTriage.text}</span>
      </div>

      <div className="text-center space-y-1 mb-4">
        <h2 className="text-2xl font-bold text-[var(--color-text-primary)]">{isHi ? 'AI परामर्श' : 'AI Consultation'}</h2>
      </div>

      {/* Chat Window */}
      <div className="bg-[var(--color-surface)] border-2 border-[var(--color-border)] rounded-xl p-4 w-full max-w-4xl flex-1 flex flex-col overflow-hidden shadow-sm">
        <div className="flex-1 overflow-y-auto space-y-3 pr-2 mb-4">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex items-start gap-3 ${msg.sender === 'user' ? 'justify-end' : ''}`}>
              {msg.sender === 'ai' && (
                <div className="h-8 w-8 rounded-full bg-[var(--color-primary-tint)] flex items-center justify-center flex-shrink-0">
                  <Bot className="h-4 w-4 text-[var(--color-primary-dark)]" />
                </div>
              )}
              <div className={`p-3 rounded-xl text-base max-w-[75%] ${msg.sender === 'ai' ? 'bg-[var(--color-primary-tint)] text-[var(--color-text-primary)] rounded-tl-none' : 'bg-[var(--color-accent-tint)] text-[var(--color-text-primary)] rounded-tr-none'}`}>
                {msg.text}
              </div>
              {msg.sender === 'user' && (
                <div className="h-8 w-8 rounded-full bg-[var(--color-accent-tint)] flex items-center justify-center flex-shrink-0">
                  <User className="h-4 w-4 text-[var(--color-accent-dark)]" />
                </div>
              )}
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>

        {/* Input Area */}
        <div className="flex gap-3">
          <button
            onClick={toggleListening}
            className={`p-4 rounded-lg border-2 transition-all ${isListening ? 'bg-[var(--color-danger)] border-[var(--color-danger)] text-white' : 'bg-[var(--color-surface)] border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[var(--color-primary)]'}`}
          >
            {isListening ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
          </button>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder={isHi ? 'अपने लक्षण यहां टाइप करें या बोलें...' : 'Type or speak your symptoms...'}
            className="flex-1 p-4 text-lg bg-[var(--color-bg)] border-2 border-[var(--color-border)] rounded-lg focus:border-[var(--color-primary)] focus:outline-none text-[var(--color-text-primary)]"
          />
          <Button onClick={handleSend} className="px-6 py-4 text-lg rounded-lg bg-[var(--color-primary-dark)] hover:bg-[var(--color-text-primary)] text-white shadow-lg">
            <Send className="h-5 w-5" />
          </Button>
        </div>
        {isListening && (
          <div className="mt-2 text-sm text-[var(--color-primary)] flex items-center gap-2">
            <div className="flex gap-1">
              <span className="w-1 h-4 bg-[var(--color-primary)] animate-pulse rounded-full"></span>
              <span className="w-1 h-4 bg-[var(--color-primary)] animate-pulse rounded-full" style={{ animationDelay: '0.1s' }}></span>
              <span className="w-1 h-4 bg-[var(--color-primary)] animate-pulse rounded-full" style={{ animationDelay: '0.2s' }}></span>
            </div>
            {isHi ? 'सुन रहा है...' : 'Listening...'}
          </div>
        )}
      </div>

      <Button onClick={onNext} className="mt-4 px-10 py-5 text-lg rounded-lg bg-[var(--color-primary-dark)] hover:bg-[var(--color-text-primary)] text-white transition-all shadow-lg min-w-[250px]">
        {isHi ? 'अगला: रिपोर्ट अपलोड करें' : 'Next: Upload Reports'}
      </Button>
    </div>
  );
}