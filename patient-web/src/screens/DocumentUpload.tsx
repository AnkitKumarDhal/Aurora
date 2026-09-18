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
  const [uploadedCount, setUploadedCount] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const cameraRequestId = useRef(0);

  useEffect(() => {
    if (!isCameraOpen || !videoRef.current || !streamRef.current) {
      return;
    }

    videoRef.current.srcObject = streamRef.current;
  }, [isCameraOpen]);

  useEffect(() => {
    return () => {
      cameraRequestId.current += 1;
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    };
  }, []);

  useEffect(() => {
    return () => {
      if (capturedImage) {
        URL.revokeObjectURL(capturedImage);
      }
    };
  }, [capturedImage]);

  const stopCamera = () => {
    cameraRequestId.current += 1;

    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setIsCameraOpen(false);
  };

  const getCameraError = (cameraError: unknown) => {
    if (!(cameraError instanceof DOMException)) {
      return isHi ? "कैमरा खोलने में त्रुटि हुई।" : "Unable to open the camera.";
    }

    if (cameraError.name === "NotAllowedError") {
      return isHi
        ? "कैमरा अनुमति नहीं मिली। कृपया इस साइट के लिए कैमरा अनुमति दें।"
        : "Camera permission was denied. Please allow camera access for this site.";
    }

    if (cameraError.name === "NotFoundError") {
      return isHi
        ? "कोई कैमरा नहीं मिला।"
        : "No camera was found on this device.";
    }

    if (cameraError.name === "NotReadableError") {
      return isHi
        ? "कैमरा किसी अन्य ऐप द्वारा उपयोग किया जा रहा है।"
        : "The camera is already in use by another application.";
    }

    if (cameraError.name === "OverconstrainedError") {
      return isHi
        ? "यह कैमरा आवश्यक सेटिंग का समर्थन नहीं करता।"
        : "The available camera does not support the requested settings.";
    }

    if (cameraError.name === "SecurityError") {
      return isHi
        ? "ब्राउज़र ने कैमरा एक्सेस रोक दिया।"
        : "The browser blocked camera access.";
    }

    return isHi ? "कैमरा खोलने में त्रुटि हुई।" : "Unable to open the camera.";
  };

  const openCamera = async () => {
    const requestId = cameraRequestId.current + 1;
    cameraRequestId.current = requestId;
    setError(null);

    try {
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;

      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error("Camera access is not supported by this browser.");
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: false,
        video: {
          facingMode: {
            ideal: "environment",
          },
        },
      });

      if (cameraRequestId.current !== requestId) {
        stream.getTracks().forEach((track) => track.stop());
        return;
      }

      streamRef.current = stream;
      setIsCameraOpen(true);
    } catch (cameraError) {
      if (cameraRequestId.current !== requestId) {
        return;
      }

      setError(getCameraError(cameraError));
    }
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
        stopCamera();
      },
      "image/png",
      0.92,
    );
  };

  const retakeImage = () => {
    setCapturedImage(null);
    setCapturedFile(null);
    setError(null);
  };

  const confirmUpload = async () => {
    if (!capturedFile || isUploading) {
      return;
    }

    stopCamera();
    setError(null);
    setIsUploading(true);

    try {
      await uploadDocument(sessionId, capturedFile, "OTHER");
      setUploadedCount((count) => count + 1);
      setCapturedImage(null);
      setCapturedFile(null);
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
            onClick={stopCamera}
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

  const hasUploadedDocuments = uploadedCount > 0;

  return (
    <div className="flex h-screen w-full flex-col items-center justify-center bg-[var(--color-bg)]">
      <div className="mb-12 space-y-4 text-center">
        <div className="mb-6 flex justify-center">
          <div className="flex h-24 w-24 items-center justify-center rounded-full bg-[var(--color-primary-tint)]">
            <Camera className="h-12 w-12 text-[var(--color-primary-dark)]" />
          </div>
        </div>

        <h2 className="text-4xl font-bold text-[var(--color-text-primary)]">
          {hasUploadedDocuments
            ? isHi
              ? "एक और रिपोर्ट जोड़ें"
              : "Add Another Report"
            : isHi
              ? "रिपोर्ट स्कैन करें"
              : "Scan Your Report"}
        </h2>

        <p className="mx-auto max-w-xl text-xl text-[var(--color-text-secondary)]">
          {hasUploadedDocuments
            ? isHi
              ? "आप चाहें तो और रिपोर्ट या प्रिस्क्रिप्शन अपलोड कर सकते हैं"
              : "You can upload more reports or prescriptions if needed"
            : isHi
              ? "अपनी पिछली रिपोर्ट या प्रिस्क्रिप्शन को कैमरे से स्कैन करें"
              : "Scan your previous report or prescription using the camera"}
        </p>
      </div>

      {error && (
        <div className="mb-6 rounded-xl border-2 border-[var(--color-danger)] bg-[var(--color-surface)] px-6 py-3 text-center text-sm font-semibold text-[var(--color-danger)]">
          {error}
        </div>
      )}

      {hasUploadedDocuments && (
        <div className="mb-6 rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3 text-center text-sm font-semibold text-[var(--color-text-secondary)]">
          {isHi
            ? `${uploadedCount} रिपोर्ट अपलोड की गई`
            : `${uploadedCount} report${uploadedCount === 1 ? "" : "s"} uploaded`}
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
          {hasUploadedDocuments
            ? isHi
              ? "एक और रिपोर्ट अपलोड करें"
              : "Upload Another Report"
            : isHi
              ? "कैमरा खोलें"
              : "Open Camera"}
        </Button>

        <Button
          className="rounded-xl border-2 border-[var(--color-border)] px-8 py-4 text-lg text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-alt)]"
          onClick={onNext}
          variant="outline"
        >
          {hasUploadedDocuments
            ? isHi
              ? "जारी रखें"
              : "Continue"
            : isHi
              ? "छोड़ दें"
              : "Skip This Step"}
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
