import { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Mic, Keyboard, Send, Square } from 'lucide-react';

interface InputPreferenceProps {
  onNext: (mode: 'voice' | 'text', content: string) => void;
  language: 'en' | 'hi';
}

export function InputPreference({ onNext, language }: InputPreferenceProps) {
  const isHi = language === 'hi';
  const [selectedMode, setSelectedMode] = useState<'voice' | 'text' | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [textInput, setTextInput] = useState('');
  const [recordingTime, setRecordingTime] = useState(0);
  const recordingInterval = useRef<ReturnType<typeof setInterval> | null>(null);

  const startRecording = () => {
    setIsRecording(true);
    setRecordingTime(0);
    recordingInterval.current = setInterval(() => setRecordingTime(prev => prev + 1), 1000);
  };

  const stopRecording = () => {
    setIsRecording(false);
    if (recordingInterval.current) clearInterval(recordingInterval.current);
    onNext('voice', 'Recorded symptom description (simulated)');
  };

  const handleTextSubmit = () => {
    if (textInput.trim()) onNext('text', textInput);
  };

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  if (selectedMode === 'voice') {
    return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col items-center justify-center w-full py-12">
        <div className="text-center space-y-4 mb-12">
          <h2 className="text-4xl font-bold text-[var(--color-text-primary)]">{isHi ? 'वॉयस परामर्श' : 'Voice Consultation'}</h2>
          <p className="text-xl text-[var(--color-text-secondary)]">{isHi ? 'माइक्रोफ़ोन पर क्लिक करें और अपने लक्षण बताएं' : 'Click the microphone and describe your symptoms'}</p>
        </div>
        <div className="bg-[var(--color-surface)] border-2 border-[var(--color-border)] rounded-2xl p-12 mb-12 flex flex-col items-center gap-8">
          <button onClick={isRecording ? stopRecording : startRecording} className={`h-32 w-32 rounded-full flex items-center justify-center transition-all ${isRecording ? 'bg-[var(--color-danger)] animate-pulse' : 'bg-[var(--color-primary)] hover:bg-[var(--color-primary-dark)]'}`}>
            {isRecording ? <Square className="h-16 w-16 text-white" /> : <Mic className="h-16 w-16 text-white" />}
          </button>
          <div className="text-3xl font-mono font-bold text-[var(--color-text-primary)]">{isRecording ? formatTime(recordingTime) : (isHi ? 'रिकॉर्ड करने के लिए टैप करें' : 'Tap to Record')}</div>
          {isRecording && (
            <div className="flex gap-2">
              {[...Array(5)].map((_, i) => (
                <motion.div key={i} className="w-2 bg-[var(--color-primary)] rounded-full" animate={{ height: [20, 60, 20] }} transition={{ duration: 0.5, repeat: Infinity, delay: i * 0.1 }} />
              ))}
            </div>
          )}
        </div>
        <Button onClick={() => setSelectedMode(null)} variant="outline" className="px-8 py-6 text-xl rounded-xl border-2 border-[var(--color-border)] text-[var(--color-text-secondary)] bg-transparent">{isHi ? 'वापस' : 'Back'}</Button>
      </motion.div>
    );
  }

  if (selectedMode === 'text') {
    return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col items-center justify-center w-full py-12">
        <div className="text-center space-y-4 mb-12">
          <h2 className="text-4xl font-bold text-[var(--color-text-primary)]">{isHi ? 'टेक्स्ट परामर्श' : 'Text Consultation'}</h2>
          <p className="text-xl text-[var(--color-text-secondary)]">{isHi ? 'नीचे अपने लक्षण टाइप करें' : 'Type your symptoms below'}</p>
        </div>
        <div className="bg-[var(--color-surface)] border-2 border-[var(--color-border)] rounded-2xl p-8 mb-12 w-full max-w-3xl">
          <textarea value={textInput} onChange={(e) => setTextInput(e.target.value)} placeholder={isHi ? "अपने लक्षण यहां वर्णित करें..." : "Describe your symptoms here..."} className="w-full h-48 p-6 text-xl bg-transparent border-2 border-[var(--color-border)] rounded-xl resize-none focus:border-[var(--color-primary)] focus:outline-none text-[var(--color-text-primary)] placeholder:text-[var(--color-text-secondary)]" />
        </div>
        <div className="flex gap-6">
          <Button onClick={() => setSelectedMode(null)} variant="outline" className="px-8 py-6 text-xl rounded-xl border-2 border-[var(--color-border)] text-[var(--color-text-secondary)] bg-transparent">{isHi ? 'वापस' : 'Back'}</Button>
          <Button onClick={handleTextSubmit} disabled={!textInput.trim()} className="px-12 py-6 text-xl rounded-xl bg-[var(--color-primary-dark)] hover:bg-[var(--color-text-primary)] text-white disabled:opacity-40 transition-all shadow-lg flex items-center gap-3">
            <Send className="h-6 w-6" /> {isHi ? 'जमा करें' : 'Submit'}
          </Button>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col items-center justify-center w-full py-12">
      <div className="text-center space-y-4 mb-12">
        <h2 className="text-4xl font-bold text-[var(--color-text-primary)]">{isHi ? 'आप कैसे परामर्श करना चाहेंगे?' : 'How would you like to consult?'}</h2>
        <p className="text-xl text-[var(--color-text-secondary)]">{isHi ? 'AI सहायक के साथ बातचीत करने का अपना पसंदीदा तरीका चुनें।' : 'Choose your preferred way to interact with the AI assistant.'}</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-4xl px-4 mb-12">
        <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} onClick={() => setSelectedMode('voice')} className="h-64 rounded-2xl border-2 border-[var(--color-border)] bg-[var(--color-surface)] hover:border-[var(--color-primary)] transition-all duration-200 flex flex-col items-center justify-center gap-6">
          <Mic className="h-16 w-16 text-[var(--color-text-secondary)]" />
          <div className="text-4xl font-semibold text-[var(--color-text-primary)]">{isHi ? 'वॉयस' : 'Voice'}</div>
          <div className="text-xl text-[var(--color-text-secondary)]">{isHi ? 'स्वाभाविक रूप से बोलें' : 'Speak naturally'}</div>
        </motion.button>
        <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} onClick={() => setSelectedMode('text')} className="h-64 rounded-2xl border-2 border-[var(--color-border)] bg-[var(--color-surface)] hover:border-[var(--color-primary)] transition-all duration-200 flex flex-col items-center justify-center gap-6">
          <Keyboard className="h-16 w-16 text-[var(--color-text-secondary)]" />
          <div className="text-4xl font-semibold text-[var(--color-text-primary)]">{isHi ? 'टेक्स्ट' : 'Text'}</div>
          <div className="text-xl text-[var(--color-text-secondary)]">{isHi ? 'अपने उत्तर टाइप करें' : 'Type your answers'}</div>
        </motion.button>
      </div>
    </motion.div>
  );
}