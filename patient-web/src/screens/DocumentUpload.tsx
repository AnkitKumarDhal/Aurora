import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Camera, RotateCcw, Check, X } from "lucide-react";

interface DocumentUploadProps {
  onNext: () => void;
  language: "en" | "hi";
}

export function DocumentUpload({ onNext, language }: DocumentUploadProps) {
  const isHi = language === "hi";
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const openCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
      });
      streamRef.current = stream;
      setIsCameraOpen(true);
    } catch (err) {
      console.error("Camera error:", err);
      alert(isHi ? "कैमरा खोलने में त्रुटि" : "Error opening camera");
    }
  };

  const closeCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
    }
    setIsCameraOpen(false);
  };

  const captureImage = () => {
    if (videoRef.current) {
      const video = videoRef.current;
      const canvas = document.createElement("canvas");
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext("2d");
      if (ctx) {
        ctx.drawImage(video, 0, 0);
        const imageDataUrl = canvas.toDataURL("image/png");
        setCapturedImage(imageDataUrl);
        closeCamera();
      }
    }
  };

  const retakeImage = () => {
    setCapturedImage(null);
  };

  const confirmUpload = () => {
    onNext();
  };

  // Camera View
  if (isCameraOpen) {
    return (
      <div className="fixed inset-0 bg-black z-50 flex flex-col">
        <div className="flex-1 relative">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            className="absolute inset-0 w-full h-full object-cover"
          />

          {/* Camera Overlay */}
          <div className="absolute inset-0 border-4 border-white border-opacity-30 m-12 rounded-3xl">
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
              <div className="w-64 h-48 border-2 border-white border-opacity-50 rounded-lg"></div>
            </div>
          </div>

          {/* Close Button */}
          <button
            onClick={closeCamera}
            className="absolute top-6 right-6 p-3 rounded-full bg-black bg-opacity-50 text-white hover:bg-opacity-70"
          >
            <X className="h-6 w-6" />
          </button>

          {/* Instructions */}
          <div className="absolute top-6 left-1/2 transform -translate-x-1/2 bg-black bg-opacity-50 text-white px-6 py-3 rounded-full">
            <p className="text-lg font-semibold">
              {isHi ? "रिपोर्ट को फ्रेम में रखें" : "Position report in frame"}
            </p>
          </div>
        </div>

        {/* Capture Button */}
        <div className="p-8 bg-black bg-opacity-80 flex justify-center">
          <button
            onClick={captureImage}
            className="h-20 w-20 rounded-full bg-white border-4 border-gray-300 flex items-center justify-center hover:scale-105 transition-transform"
          >
            <div className="h-16 w-16 rounded-full bg-white"></div>
          </button>
        </div>
      </div>
    );
  }

  // Preview Captured Image
  if (capturedImage) {
    return (
      <div className="flex flex-col items-center justify-center w-full h-screen bg-[var(--color-bg)]">
        <div className="text-center space-y-4 mb-6">
          <h2 className="text-3xl font-bold text-[var(--color-text-primary)]">
            {isHi ? "रिपोर्ट स्कैन की गई" : "Report Scanned"}
          </h2>
          <p className="text-xl text-[var(--color-text-secondary)]">
            {isHi ? "क्या यह ठीक है?" : "Does this look good?"}
          </p>
        </div>

        <div className="bg-[var(--color-surface)] border-2 border-[var(--color-border)] rounded-2xl p-6 mb-8 shadow-lg">
          <img
            src={capturedImage}
            alt="Captured document"
            className="max-w-2xl max-h-96 rounded-lg object-contain"
          />
        </div>

        <div className="flex gap-6">
          <Button
            onClick={retakeImage}
            variant="outline"
            className="px-8 py-6 text-xl rounded-xl border-2 border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-alt)] flex items-center gap-3"
          >
            <RotateCcw className="h-6 w-6" />
            {isHi ? "पुनः लें" : "Retake"}
          </Button>
          <Button
            onClick={confirmUpload}
            className="px-10 py-6 text-xl rounded-xl bg-[var(--color-primary-dark)] hover:bg-[var(--color-text-primary)] text-white transition-all shadow-lg flex items-center gap-3"
          >
            <Check className="h-6 w-6" />
            {isHi ? "पुष्टि करें" : "Confirm"}
          </Button>
        </div>
      </div>
    );
  }

  // Initial Screen - Just Camera Button
  return (
    <div className="flex flex-col items-center justify-center w-full h-screen bg-[var(--color-bg)]">
      <div className="text-center space-y-4 mb-12">
        <div className="flex justify-center mb-6">
          <div className="h-24 w-24 rounded-full bg-[var(--color-primary-tint)] flex items-center justify-center">
            <Camera className="h-12 w-12 text-[var(--color-primary-dark)]" />
          </div>
        </div>
        <h2 className="text-4xl font-bold text-[var(--color-text-primary)]">
          {isHi ? "रिपोर्ट स्कैन करें" : "Scan Your Report"}
        </h2>
        <p className="text-xl text-[var(--color-text-secondary)] max-w-xl mx-auto">
          {isHi
            ? "अपनी पिछली रिपोर्ट या प्रिस्क्रिप्शन को कैमरे से स्कैन करें"
            : "Scan your previous report or prescription using the camera"}
        </p>
      </div>

      <div className="flex flex-col items-center gap-6">
        <Button
          onClick={openCamera}
          className="px-12 py-8 text-2xl rounded-2xl bg-[var(--color-primary-dark)] hover:bg-[var(--color-text-primary)] text-white transition-all shadow-xl flex items-center gap-4 min-w-[300px]"
        >
          <Camera className="h-8 w-8" />
          {isHi ? "कैमरा खोलें" : "Open Camera"}
        </Button>

        <Button
          onClick={onNext}
          variant="outline"
          className="px-8 py-4 text-lg rounded-xl border-2 border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-alt)]"
        >
          {isHi ? "छोड़ दें" : "Skip This Step"}
        </Button>
      </div>

      <p className="text-lg text-[var(--color-text-secondary)] mt-8">
        {isHi
          ? "रिपोर्ट को साफ और अच्छी रोशनी में रखें"
          : "Keep report clear and in good lighting"}
      </p>
    </div>
  );
}
