import { useState } from 'react';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { User, Fingerprint, ArrowLeft } from 'lucide-react';

interface IdentitySelectionProps {
  onNext: (identityType: 'abha' | 'aadhaar', number: string) => void;
  language: 'en' | 'hi';
}

export function IdentitySelection({ onNext, language }: IdentitySelectionProps) {
  const isHi = language === 'hi';
  const [selectedId, setSelectedId] = useState<'abha' | 'aadhaar' | null>(null);
  const [showInput, setShowInput] = useState(false);
  const [idNumber, setIdNumber] = useState('');
  const [useBiometric, setUseBiometric] = useState(false);

  const handleIdSelect = (type: 'abha' | 'aadhaar') => {
    setSelectedId(type);
    setShowInput(true);
  };

  const handleContinue = () => {
    const requiredLength = selectedId === 'abha' ? 14 : 12;
    if (idNumber.length >= requiredLength || useBiometric) {
      onNext(selectedId!, idNumber);
    }
  };

  const handleBack = () => {
    setShowInput(false);
    setSelectedId(null);
    setIdNumber('');
    setUseBiometric(false);
  };

  const handleNumberInput = (num: string) => {
    const maxLength = selectedId === 'abha' ? 14 : 12;
    if (idNumber.length < maxLength) {
      setIdNumber(idNumber + num);
    }
  };

  const handleDelete = () => setIdNumber(idNumber.slice(0, -1));
  const handleClear = () => setIdNumber('');

  // --- INPUT SCREEN ---
  if (showInput) {
    const maxLength = selectedId === 'abha' ? 14 : 12;
    const displayNumber = idNumber.replace(/(\d{4})(?=\d)/g, '$1 ');

    return (
      <div className="flex flex-col items-center justify-center w-full h-screen overflow-hidden bg-[var(--color-bg)]">
        {/* Back Button */}
        <button onClick={handleBack} className="absolute top-8 left-8 p-2 rounded-full hover:bg-[var(--color-surface-alt)] transition-colors">
          <ArrowLeft className="h-6 w-6 text-[var(--color-text-secondary)]" />
        </button>

        {/* Header */}
        <div className="text-center space-y-2 mb-8">
          <h2 className="text-4xl font-bold text-[var(--color-text-primary)]">
            {isHi ? `${selectedId === 'abha' ? 'ABHA' : 'आधार'} नंबर दर्ज करें` : `Enter ${selectedId === 'abha' ? 'ABHA' : 'Aadhaar'} Number`}
          </h2>
          <p className="text-lg text-[var(--color-text-secondary)]">
            {selectedId === 'abha' ? (isHi ? '14-अंकीय ABHA नंबर' : '14-digit ABHA number') : (isHi ? '12-अंकीय आधार नंबर' : '12-digit Aadhaar number')}
          </p>
        </div>

        {/* Input Display */}
        <div className="bg-[var(--color-surface)] border-2 border-[var(--color-border)] rounded-2xl p-6 mb-8 w-full max-w-xl shadow-lg">
          <div className="text-center text-4xl font-mono font-bold text-[var(--color-text-primary)] tracking-widest min-h-[70px] flex items-center justify-center">
            {displayNumber || <span className="text-[var(--color-border)]">_ _ _ _  _ _ _ _  _ _ _ _  _ _</span>}
          </div>
        </div>

        {/* Compact Keypad */}
        <div className="grid grid-cols-3 gap-3 mb-6">
          {['1', '2', '3', '4', '5', '6', '7', '8', '9'].map((num) => (
            <motion.button
              key={num}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => handleNumberInput(num)}
              className="w-24 h-16 rounded-xl bg-[var(--color-surface)] border-2 border-[var(--color-border)] text-2xl font-bold text-[var(--color-text-primary)] hover:border-[var(--color-primary)] hover:bg-[var(--color-primary-tint)] transition-all shadow-md"
            >
              {num}
            </motion.button>
          ))}
          <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} onClick={handleClear} className="w-24 h-16 rounded-xl bg-[var(--color-surface)] border-2 border-[var(--color-danger)] text-base font-semibold text-[var(--color-danger)] hover:bg-[var(--color-danger)] hover:text-white transition-all shadow-md">
            Clear
          </motion.button>
          <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} onClick={() => handleNumberInput('0')} className="w-24 h-16 rounded-xl bg-[var(--color-surface)] border-2 border-[var(--color-border)] text-2xl font-bold text-[var(--color-text-primary)] hover:border-[var(--color-primary)] hover:bg-[var(--color-primary-tint)] transition-all shadow-md">
            0
          </motion.button>
          <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} onClick={handleDelete} className="w-24 h-16 rounded-xl bg-[var(--color-surface)] border-2 border-[var(--color-border)] text-xl font-semibold text-[var(--color-text-secondary)] hover:bg-[var(--color-warning)] hover:text-white transition-all shadow-md">
            ←
          </motion.button>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4">
          <Button onClick={() => setUseBiometric(!useBiometric)} className={`px-6 py-4 text-lg rounded-xl transition-all ${useBiometric ? 'bg-[var(--color-primary)] text-white shadow-lg' : 'bg-transparent border-2 border-[var(--color-border)] text-[var(--color-text-secondary)]'}`}>
            <Fingerprint className="h-5 w-5 mr-2 inline" /> {isHi ? 'बायोमेट्रिक' : 'Biometric'}
          </Button>
          <Button onClick={handleContinue} disabled={idNumber.length < maxLength && !useBiometric} className="px-8 py-4 text-lg rounded-xl bg-[var(--color-primary-dark)] hover:bg-[var(--color-text-primary)] text-white disabled:opacity-40 transition-all shadow-lg">
            {isHi ? 'जारी रखें' : 'Continue'}
          </Button>
        </div>
      </div>
    );
  }

  // --- SELECTION SCREEN ---
  return (
    <div className="flex flex-col items-center justify-center w-full h-screen overflow-hidden">
      <div className="text-center space-y-4 mb-12">
        <h2 className="text-4xl font-bold text-[var(--color-text-primary)]">{isHi ? 'पहचान का तरीका चुनें' : 'Select Identification Method'}</h2>
        <p className="text-xl text-[var(--color-text-secondary)]">{isHi ? 'आप अपनी पहचान कैसे दर्ज करना चाहेंगे?' : 'How would you like to identify yourself?'}</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-4xl px-4">
        <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} onClick={() => handleIdSelect('abha')} className={`h-64 rounded-2xl border-2 transition-all duration-200 flex flex-col items-center justify-center gap-6 ${selectedId === 'abha' ? 'border-[var(--color-primary)] bg-[var(--color-primary-tint)] shadow-lg' : 'border-[var(--color-border)] bg-[var(--color-surface)] hover:border-[var(--color-primary)]'}`}>
          <User className={`h-16 w-16 ${selectedId === 'abha' ? 'text-[var(--color-primary-dark)]' : 'text-[var(--color-text-secondary)]'}`} />
          <div className="text-3xl font-semibold text-[var(--color-text-primary)]">ABHA</div>
          <div className="text-lg text-[var(--color-text-secondary)]">{isHi ? '14-अंकीय ABHA नंबर' : '14-digit ABHA Number'}</div>
        </motion.button>
        <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} onClick={() => handleIdSelect('aadhaar')} className={`h-64 rounded-2xl border-2 transition-all duration-200 flex flex-col items-center justify-center gap-6 ${selectedId === 'aadhaar' ? 'border-[var(--color-primary)] bg-[var(--color-primary-tint)] shadow-lg' : 'border-[var(--color-border)] bg-[var(--color-surface)] hover:border-[var(--color-primary)]'}`}>
          <Fingerprint className={`h-16 w-16 ${selectedId === 'aadhaar' ? 'text-[var(--color-primary-dark)]' : 'text-[var(--color-text-secondary)]'}`} />
          <div className="text-3xl font-semibold text-[var(--color-text-primary)]">{isHi ? 'आधार' : 'Aadhaar'}</div>
          <div className="text-lg text-[var(--color-text-secondary)]">{isHi ? '12-अंकीय आधार / बायोमेट्रिक' : '12-digit Aadhaar / Biometric'}</div>
        </motion.button>
      </div>
    </div>
  );
}