import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { ShieldCheck, FileText } from 'lucide-react';

interface ConsentScreenProps {
  onNext: () => void;
  onDecline: () => void;
  language: 'en' | 'hi';
}

export function ConsentScreen({ onNext, onDecline, language }: ConsentScreenProps) {
  const isHi = language === 'hi';

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col items-center justify-center w-full py-12">
      <div className="text-center space-y-4 mb-12">
        <div className="flex justify-center mb-6">
          <div className="h-20 w-20 rounded-full bg-[var(--color-primary-tint)] flex items-center justify-center">
            <ShieldCheck className="h-10 w-10 text-[var(--color-primary-dark)]" />
          </div>
        </div>
        <h2 className="text-4xl font-bold text-[var(--color-text-primary)]">{isHi ? 'रोगी सहमति' : 'Patient Consent'}</h2>
        <p className="text-xl text-[var(--color-text-secondary)] max-w-2xl mx-auto">
          {isHi ? 'आपको सर्वोत्तम देखभाल प्रदान करने के लिए, औरोरा को आपके चिकित्सा इतिहास तक पहुंच की आवश्यकता है।' : 'To provide you with the best care, Aurora needs to access your medical history and share it with the consulting doctor.'}
        </p>
      </div>

      <div className="bg-[var(--color-surface)] border-2 border-[var(--color-border)] rounded-2xl p-8 max-w-3xl w-full mb-12 shadow-sm">
        <div className="flex items-start gap-4">
          <FileText className="h-6 w-6 text-[var(--color-text-secondary)] mt-1 flex-shrink-0" />
          <div className="space-y-4 text-lg text-[var(--color-text-primary)]">
            <p>{isHi ? 'आगे बढ़कर, आप निम्नलिखित से सहमत होते हैं:' : 'By proceeding, you agree to the following:'}</p>
            <ul className="list-disc list-inside space-y-2 text-[var(--color-text-secondary)]">
              <li>{isHi ? 'औरोरा सुरक्षित रूप से ABHA/आधार के माध्यम से आपके रिकॉर्ड प्राप्त करेगा।' : 'Aurora will securely fetch your records via ABHA/Aadhaar.'}</li>
              <li>{isHi ? 'आपका डेटा केवल उपस्थित डॉक्टर के साथ साझा किया जाएगा।' : 'Your data will be shared only with the attending doctor.'}</li>
              <li>{isHi ? 'सभी डेटा एन्क्रिप्टेड और HIPAA/DPDP अनुपालन है।' : 'All data is encrypted and HIPAA/DPDP compliant.'}</li>
            </ul>
          </div>
        </div>
      </div>

      <div className="flex gap-6">
        <Button onClick={onDecline} className="px-10 py-6 text-xl rounded-xl border-2 border-[var(--color-danger)] text-[var(--color-danger)] hover:bg-[var(--color-danger)] hover:text-white transition-all min-w-[200px] bg-transparent">
          {isHi ? 'अस्वीकार करें' : 'Decline'}
        </Button>
        <Button onClick={onNext} className="px-12 py-6 text-xl rounded-xl bg-[var(--color-primary-dark)] hover:bg-[var(--color-text-primary)] text-white transition-all shadow-lg min-w-[280px]">
          {isHi ? 'मैं सहमत हूं' : 'I Consent'}
        </Button>
      </div>
    </motion.div>
  );
}