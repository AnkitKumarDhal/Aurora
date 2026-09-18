import { useEffect, useRef, useState } from "react";
import { uploadDocument } from "@/api/documents";
import { Button } from "@/components/ui/button";
import { Camera, Check, Loader2, RotateCcw, X } from "lucide-react";

interface DocumentUploadProps {
  sessionId: string;
  onNext: () => void;
  language: "en" | "hi";
}

export function DocumentUpload({
  sessionId,
  onNext,
  language,
}: DocumentUploadProps) {
  const isHi = language === "hi";
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [capturedFile, setCapturedFile] = useState<File | null>(null);
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    if (isCameraOpen && videoRef.current && streamRef.current) {
      videoRef.current.srcObject = streamRef.current;
    }
  }, [isCameraOpen]);

  useEffect(() => {
    return () => {
      if (capturedImage) {
        URL.revokeObjectURL(capturedImage);
      }

      streamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, [capturedImage]);

  const openCamera = async () => {
    setError(null);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "environment",
        },
      });

      streamRef.current = stream;
      setIsCameraOpen(true);
    } catch {
      setError(isHi ? "कैमरा खोलने में त्रुटि हुई।" : "Unable to open the camera.");
    }
  };

  const closeCamera = () => {
    streamRef.current?.getTracks().forEach((track) => track.stop());

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    streamRef.current = null;
    setIsCameraOpen(false);
  };

  const captureImage = () => {
    const video = videoRef.current;

    if (!video || video.videoWidth === 0 || video.videoHeight === 0) {
      setError(isHi ? "कैमरा अभी तैयार नहीं है।" : "The camera is not ready yet.");
      return;
    }

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const context = canvas.getContext("2d");

    if (!context) {
      setError(
        isHi ? "रिपोर्ट कैप्चर नहीं हो सकी।" : "Unable to capture the report.",
      );
      return;
    }

    context.drawImage(video, 0, 0, video.videoWidth, video.videoHeight);

    canvas.toBlob(
      (blob) => {
        if (!blob) {
          setError(
            isHi ? "रिपोर्ट कैप्चर नहीं हो सकी।" : "Unable to capture the report.",
          );
          return;
        }

        const filename = `aurora-report-${Date.now()}.png`;

        setCapturedFile(
          new File([blob], filename, {
            type: "image/png",
          }),
        );
        setCapturedImage(URL.createObjectURL(blob));
        setError(null);
        closeCamera();
      },
      "image/png",
      0.92,
    );
  };

  const retakeImage = () => {
    if (capturedImage) {
      URL.revokeObjectURL(capturedImage);
    }

    setCapturedImage(null);
    setCapturedFile(null);
    setError(null);
  };

  const confirmUpload = async () => {
    if (!capturedFile || isUploading) {
      return;
    }

    setError(null);
    setIsUploading(true);

    try {
      await uploadDocument(sessionId, capturedFile, "OTHER");

      onNext();
    } catch (uploadError) {
      setError(
        uploadError instanceof Error
          ? uploadError.message
          : isHi
            ? "रिपोर्ट अपलोड नहीं हो सकी।"
            : "Unable to upload the report.",
      );
    } finally {
      setIsUploading(false);
    }
  };

  if (isCameraOpen) {
    return (
      <div className="fixed inset-0 z-50 flex flex-col bg-black">
        <div className="relative flex-1">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            className="absolute inset-0 h-full w-full object-cover"
          />

          <div className="absolute inset-0 m-12 rounded-3xl border-4 border-white border-opacity-30">
            <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
              <div className="h-48 w-64 rounded-lg border-2 border-white border-opacity-50" />
            </div>
          </div>

          <button
            className="absolute right-6 top-6 rounded-full bg-black bg-opacity-50 p-3 text-white hover:bg-opacity-70"
            onClick={closeCamera}
            type="button"
          >
            <X className="h-6 w-6" />
          </button>

          <div className="absolute left-1/2 top-6 -translate-x-1/2 rounded-full bg-black bg-opacity-50 px-6 py-3 text-white">
            <p className="text-lg font-semibold">
              {isHi ? "रिपोर्ट को फ्रेम में रखें" : "Position report in frame"}
            </p>
          </div>
        </div>

        <div className="flex justify-center bg-black bg-opacity-80 p-8">
          <button
            className="flex h-20 w-20 items-center justify-center rounded-full border-4 border-gray-300 bg-white transition-transform hover:scale-105"
            onClick={captureImage}
            type="button"
          >
            <div className="h-16 w-16 rounded-full bg-white" />
          </button>
        </div>
      </div>
    );
  }

  if (capturedImage) {
    return (
      <div className="flex h-screen w-full flex-col items-center justify-center bg-[var(--color-bg)]">
        <div className="mb-6 space-y-4 text-center">
          <h2 className="text-3xl font-bold text-[var(--color-text-primary)]">
            {isHi ? "रिपोर्ट स्कैन की गई" : "Report Scanned"}
          </h2>

          <p className="text-xl text-[var(--color-text-secondary)]">
            {isHi ? "क्या यह ठीक है?" : "Does this look good?"}
          </p>
        </div>

        <div className="mb-8 rounded-2xl border-2 border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-lg">
          <img
            src={capturedImage}
            alt="Captured document"
            className="max-h-96 max-w-2xl rounded-lg object-contain"
          />
        </div>

        {error && (
          <div className="mb-5 rounded-xl border-2 border-[var(--color-danger)] bg-[var(--color-surface)] px-6 py-3 text-center text-sm font-semibold text-[var(--color-danger)]">
            {error}
          </div>
        )}

        <div className="flex gap-6">
          <Button
            className="flex items-center gap-3 rounded-xl border-2 border-[var(--color-border)] px-8 py-6 text-xl text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-alt)]"
            disabled={isUploading}
            onClick={retakeImage}
            variant="outline"
          >
            <RotateCcw className="h-6 w-6" />
            {isHi ? "पुनः लें" : "Retake"}
          </Button>

          <Button
            className="flex items-center gap-3 rounded-xl bg-[var(--color-primary-dark)] px-10 py-6 text-xl text-white shadow-lg transition-all hover:bg-[var(--color-text-primary)]"
            disabled={isUploading}
            onClick={() => {
              void confirmUpload();
            }}
          >
            {isUploading ? (
              <Loader2 className="h-6 w-6 animate-spin" />
            ) : (
              <Check className="h-6 w-6" />
            )}

            {isUploading
              ? isHi
                ? "अपलोड हो रहा है..."
                : "Uploading..."
              : isHi
                ? "पुष्टि करें"
                : "Upload Report"}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen w-full flex-col items-center justify-center bg-[var(--color-bg)]">
      <div className="mb-12 space-y-4 text-center">
        <div className="mb-6 flex justify-center">
          <div className="flex h-24 w-24 items-center justify-center rounded-full bg-[var(--color-primary-tint)]">
            <Camera className="h-12 w-12 text-[var(--color-primary-dark)]" />
          </div>
        </div>

        <h2 className="text-4xl font-bold text-[var(--color-text-primary)]">
          {isHi ? "रिपोर्ट स्कैन करें" : "Scan Your Report"}
        </h2>

        <p className="mx-auto max-w-xl text-xl text-[var(--color-text-secondary)]">
          {isHi
            ? "अपनी पिछली रिपोर्ट या प्रिस्क्रिप्शन को कैमरे से स्कैन करें"
            : "Scan your previous report or prescription using the camera"}
        </p>
      </div>

      {error && (
        <div className="mb-6 rounded-xl border-2 border-[var(--color-danger)] bg-[var(--color-surface)] px-6 py-3 text-center text-sm font-semibold text-[var(--color-danger)]">
          {error}
        </div>
      )}

      <div className="flex flex-col items-center gap-6">
        <Button
          className="flex min-w-[300px] items-center gap-4 rounded-2xl bg-[var(--color-primary-dark)] px-12 py-8 text-2xl text-white shadow-xl transition-all hover:bg-[var(--color-text-primary)]"
          onClick={() => {
            void openCamera();
          }}
        >
          <Camera className="h-8 w-8" />
          {isHi ? "कैमरा खोलें" : "Open Camera"}
        </Button>

        <Button
          className="rounded-xl border-2 border-[var(--color-border)] px-8 py-4 text-lg text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-alt)]"
          onClick={onNext}
          variant="outline"
        >
          {isHi ? "छोड़ दें" : "Skip This Step"}
        </Button>
      </div>

      <p className="mt-8 text-lg text-[var(--color-text-secondary)]">
        {isHi
          ? "रिपोर्ट को साफ और अच्छी रोशनी में रखें"
          : "Keep report clear and in good lighting"}
      </p>
    </div>
  );
}
