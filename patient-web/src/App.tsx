import { useState, useEffect } from 'react';
import { Moon, Sun } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { LanguageSelection } from './screens/LanguageSelection';
import { WelcomeScreen } from './screens/WelcomeScreen';
import { IdentitySelection } from './screens/IdentitySelection';
import { ConsentScreen } from './screens/ConsentScreen';
import { VoiceAIConsultation } from './screens/VoiceAIConsultation';
import { TextAIConsultation } from './screens/TextAIConsultation';
import { DocumentUpload } from './screens/DocumentUpload';
import { WaitingScreen } from './screens/WaitingScreen';

export default function App() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [currentScreen, setCurrentScreen] = useState('language');
  const [lang, setLang] = useState<'en' | 'hi'>('en');
  const [consultationMode, setConsultationMode] = useState<'voice' | 'text' | null>(null);

  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  const resetFlow = () => {
    setCurrentScreen('language');
    setLang('en');
    setConsultationMode(null);
  };

  return (
    <div className="min-h-screen bg-[var(--color-bg)] text-[var(--color-text-primary)] transition-colors duration-300">
      <header className="flex items-center justify-between p-6 border-b border-[var(--color-border)]">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] flex items-center justify-center">
            <span className="text-white font-bold text-sm">A</span>
          </div>
          <h1 className="text-xl font-semibold text-[var(--color-text-primary)]">Aurora</h1>
        </div>
        
        <Button 
          variant="outline" 
          size="icon" 
          onClick={toggleTheme}
          className="rounded-full border-[var(--color-border)] bg-[var(--color-surface)]"
        >
          {theme === 'light' ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
        </Button>
      </header>

      <main className="container mx-auto max-w-5xl p-6 md:p-12">
        {currentScreen === 'language' && (
          <LanguageSelection 
            onNext={(selectedLang) => { 
              setLang(selectedLang); 
              setCurrentScreen('welcome'); 
            }} 
          />
        )}
        
        {currentScreen === 'welcome' && (
          <WelcomeScreen 
            onNext={() => setCurrentScreen('identity')} 
            language={lang} 
          />
        )}
        
        {currentScreen === 'identity' && (
          <IdentitySelection 
            onNext={(identityType, number) => {
              console.log('Identity:', identityType, number);
              setCurrentScreen('consent');
            }}
            language={lang}
          />
        )}
        
        {currentScreen === 'consent' && (
          <ConsentScreen 
            onNext={() => setCurrentScreen('ai-mode')} 
            onDecline={resetFlow}
            language={lang}
          />
        )}

        {currentScreen === 'ai-mode' && (
          <div className="flex flex-col items-center justify-center h-[75vh]">
            <div className="text-center space-y-4 mb-12">
              <h2 className="text-4xl font-bold text-[var(--color-text-primary)]">
                {lang === 'hi' ? 'कैसे परामर्श करना चाहेंगे?' : 'How would you like to consult?'}
              </h2>
              <p className="text-xl text-[var(--color-text-secondary)]">
                {lang === 'hi' ? 'AI सहायक के साथ बातचीत का अपना तरीका चुनें' : 'Choose your preferred way to interact with AI'}
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-4xl px-4">
              <button
                onClick={() => {
                  setConsultationMode('voice');
                  setCurrentScreen('ai-voice');
                }}
                className="h-64 rounded-2xl border-2 border-[var(--color-border)] bg-[var(--color-surface)] hover:border-[var(--color-primary)] transition-all flex flex-col items-center justify-center gap-6"
              >
                <div className="h-20 w-20 rounded-full bg-[var(--color-primary-tint)] flex items-center justify-center">
                  <svg className="h-10 w-10 text-[var(--color-primary-dark)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                  </svg>
                </div>
                <div className="text-3xl font-semibold text-[var(--color-text-primary)]">
                  {lang === 'hi' ? 'वॉयस' : 'Voice'}
                </div>
                <div className="text-lg text-[var(--color-text-secondary)]">
                  {lang === 'hi' ? 'बोलकर बताएं' : 'Speak naturally'}
                </div>
              </button>

              <button
                onClick={() => {
                  setConsultationMode('text');
                  setCurrentScreen('ai-text');
                }}
                className="h-64 rounded-2xl border-2 border-[var(--color-border)] bg-[var(--color-surface)] hover:border-[var(--color-primary)] transition-all flex flex-col items-center justify-center gap-6"
              >
                <div className="h-20 w-20 rounded-full bg-[var(--color-primary-tint)] flex items-center justify-center">
                  <svg className="h-10 w-10 text-[var(--color-primary-dark)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                </div>
                <div className="text-3xl font-semibold text-[var(--color-text-primary)]">
                  {lang === 'hi' ? 'टेक्स्ट' : 'Text'}
                </div>
                <div className="text-lg text-[var(--color-text-secondary)]">
                  {lang === 'hi' ? 'टाइप करके बताएं' : 'Type your symptoms'}
                </div>
              </button>
            </div>
          </div>
        )}
        
        {currentScreen === 'ai-voice' && consultationMode === 'voice' && (
          <VoiceAIConsultation 
            onNext={() => setCurrentScreen('upload')}
            language={lang}
          />
        )}

        {currentScreen === 'ai-text' && consultationMode === 'text' && (
          <TextAIConsultation 
            onNext={() => setCurrentScreen('upload')}
            language={lang}
          />
        )}
        
        {currentScreen === 'upload' && (
          <DocumentUpload 
            onNext={() => setCurrentScreen('waiting')}
            language={lang}
          />
        )}
        
        {currentScreen === 'waiting' && (
          <WaitingScreen 
            onReset={resetFlow}
            language={lang}
          />
        )}
      </main>
    </div>
  );
}