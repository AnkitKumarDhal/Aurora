import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Bot, User, Send, AlertTriangle, CheckCircle, Clock } from 'lucide-react';

interface TextAIConsultationProps {
  onNext: () => void;
  language: 'en' | 'hi';
}

interface Message {
  id: number;
  sender: 'ai' | 'user';
  text: string;
}

export function TextAIConsultation({ onNext, language }: TextAIConsultationProps) {
  const isHi = language === 'hi';
  const [messages, setMessages] = useState<Message[]>([
    { id: 1, sender: 'ai', text: isHi ? 'नमस्ते! मैं औरोरा AI हूं। कृपया अपने लक्षण बताएं।' : 'Hello! I am Aurora AI. Please describe your symptoms.' }
  ]);
  const [input, setInput] = useState('');
  const [triageLevel, setTriageLevel] = useState<'none' | 'green' | 'yellow' | 'red'>('none');
  const [isTyping, setIsTyping] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const messageCount = useRef(0);

  const aiQuestions = [
    isHi ? 'कब से ये लक्षण हैं?' : 'How long have you had these symptoms?',
    isHi ? 'क्या कोई अन्य लक्षण हैं?' : 'Are there any other symptoms?',
    isHi ? 'क्या आप कोई दवा ले रहे हैं?' : 'Are you taking any medications?',
    isHi ? 'क्या आपको कोई पुरानी बीमारी है?' : 'Do you have any chronic illnesses?',
    isHi ? 'धन्यवाद। आप अब अपनी रिपोर्ट अपलोड कर सकते हैं।' : 'Thank you. You can now proceed to upload your reports.'
  ];

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSend = () => {
    if (!input.trim()) return;

    const userMsg: Message = { id: Date.now(), sender: 'user', text: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    messageCount.current += 1;

    const lowerText = input.toLowerCase();
    if (lowerText.includes('chest pain') || lowerText.includes('heart') || lowerText.includes('bleeding') || lowerText.includes('can\'t breathe') || lowerText.includes('severe') || lowerText.includes('छाती') || lowerText.includes('सांस')) {
      setTriageLevel('red');
    } else if (lowerText.includes('fever') || lowerText.includes('cough') || lowerText.includes('pain') || lowerText.includes('बुखार') || lowerText.includes('दर्द')) {
      if (triageLevel === 'none') setTriageLevel('yellow');
    } else {
      if (triageLevel === 'none') setTriageLevel('green');
    }

    setIsTyping(true);

    setTimeout(() => {
      const questionIndex = Math.min(messageCount.current - 1, aiQuestions.length - 1);
      const aiResponse: Message = { 
        id: Date.now() + 1, 
        sender: 'ai', 
        text: aiQuestions[questionIndex]
      };
      setMessages(prev => [...prev, aiResponse]);
      setIsTyping(false);
    }, 1500);
  };

  const triageConfig = {
    none: { color: 'bg-gray-300', text: isHi ? 'विश्लेषण...' : 'Analyzing...', icon: null, hidden: true },
    green: { color: 'bg-[var(--color-success)]', text: isHi ? 'नियमित (Routine)' : 'Routine', icon: CheckCircle, hidden: false },
    yellow: { color: 'bg-[var(--color-warning)]', text: isHi ? 'तत्काल (Urgent)' : 'Urgent', icon: Clock, hidden: false },
    red: { color: 'bg-[var(--color-danger)] animate-pulse', text: isHi ? 'आपातकालीन (Emergency)' : '🚨 EMERGENCY', icon: AlertTriangle, hidden: false },
  };

  const currentTriage = triageConfig[triageLevel];

  return (
    <div className="flex flex-col items-center w-full h-[80vh]">
      {!currentTriage.hidden && (
        <div className={`w-full max-w-3xl mb-4 p-3 rounded-lg ${currentTriage.color} text-white flex items-center justify-center gap-3 shadow-lg transition-all duration-500`}>
          {currentTriage.icon && <currentTriage.icon className="h-5 w-5" />}
          <span className="text-xl font-bold">{currentTriage.text}</span>
        </div>
      )}

      <div className="text-center mb-4">
        <h2 className="text-2xl font-bold text-[var(--color-text-primary)]">{isHi ? 'AI टेक्स्ट परामर्श' : 'AI Text Consultation'}</h2>
        <p className="text-sm text-[var(--color-text-secondary)]">{isHi ? 'अपने लक्षण टाइप करें और एंटर दबाएं' : 'Type your symptoms and press Enter'}</p>
      </div>

      <div className="bg-[var(--color-surface)] border-2 border-[var(--color-border)] rounded-xl p-4 w-full max-w-3xl flex-1 flex flex-col overflow-hidden shadow-sm">
        <div className="flex-1 overflow-y-auto space-y-3 pr-2 mb-4">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex items-start gap-3 ${msg.sender === 'user' ? 'justify-end' : ''}`}>
              {msg.sender === 'ai' && (
                <div className="h-8 w-8 rounded-full bg-[var(--color-primary-tint)] flex items-center justify-center flex-shrink-0">
                  <Bot className="h-4 w-4 text-[var(--color-primary-dark)]" />
                </div>
              )}
              <div className={`p-3 rounded-xl text-base max-w-[80%] ${msg.sender === 'ai' ? 'bg-[var(--color-primary-tint)] text-[var(--color-text-primary)] rounded-tl-none' : 'bg-[var(--color-accent-tint)] text-[var(--color-text-primary)] rounded-tr-none'}`}>
                {msg.text}
              </div>
              {msg.sender === 'user' && (
                <div className="h-8 w-8 rounded-full bg-[var(--color-accent-tint)] flex items-center justify-center flex-shrink-0">
                  <User className="h-4 w-4 text-[var(--color-accent-dark)]" />
                </div>
              )}
            </div>
          ))}
          {isTyping && (
            <div className="flex items-start gap-3">
              <div className="h-8 w-8 rounded-full bg-[var(--color-primary-tint)] flex items-center justify-center flex-shrink-0">
                <Bot className="h-4 w-4 text-[var(--color-primary-dark)]" />
              </div>
              <div className="p-3 rounded-xl bg-[var(--color-primary-tint)] rounded-tl-none flex gap-1">
                <span className="w-2 h-2 bg-[var(--color-text-secondary)] rounded-full animate-bounce"></span>
                <span className="w-2 h-2 bg-[var(--color-text-secondary)] rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                <span className="w-2 h-2 bg-[var(--color-text-secondary)] rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></span>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        <div className="flex gap-3">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder={isHi ? 'अपने लक्षण यहां टाइप करें...' : 'Type your symptoms here...'}
            className="flex-1 p-4 text-lg bg-[var(--color-bg)] border-2 border-[var(--color-border)] rounded-lg focus:border-[var(--color-primary)] focus:outline-none text-[var(--color-text-primary)]"
          />
          <Button onClick={handleSend} className="px-6 py-4 text-lg rounded-lg bg-[var(--color-primary-dark)] hover:bg-[var(--color-text-primary)] text-white shadow-lg">
            <Send className="h-5 w-5" />
          </Button>
        </div>
      </div>

      <Button onClick={onNext} className="mt-4 px-10 py-5 text-lg rounded-lg bg-[var(--color-primary-dark)] hover:bg-[var(--color-text-primary)] text-white transition-all shadow-lg">
        {isHi ? 'अगला: रिपोर्ट अपलोड' : 'Next: Upload Reports'}
      </Button>
    </div>
  );
}