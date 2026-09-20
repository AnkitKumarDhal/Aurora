import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Camera, Check, FileUp, Loader2, RotateCcw, X } from "lucide-react";
import {
  savePatientDraftDocument,
  type PatientDraftDocument,
} from "@/lib/patientDraft";

interface DocumentUploadProps {
  draftId: string;
  onNext: () => void;
  language: "en" | "hi";
  onActivity: () => void;
}

export function DocumentUpload({
  draftId,
  onNext,
  language,
  onActivity,
}: DocumentUploadProps) {
  const isHi = language === "hi";
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [capturedFile, setCapturedFile] = useState<File | null>(null);
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [uploadedCount, setUploadedCount] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const cameraRequestId = useRef(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

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
        ? "कैमरा अनुमति नहीं मिली। कृपया इस साइट के लिए कैमरा अनुमति दें या रिपोर्ट अपलोड करें।"
        : "Camera permission was denied. Please allow camera access for this site or upload the report instead.";
    }

    if (cameraError.name === "NotFoundError") {
      return isHi
        ? "कोई कैमरा नहीं मिला। आप रिपोर्ट अपलोड कर सकते हैं।"
        : "No camera was found on this device. You can upload the report instead.";
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
        ? "ब्राउज़र ने कैमरा एक्सेस रोक दिया। HTTPS का उपयोग करें या रिपोर्ट अपलोड करें।"
        : "The browser blocked camera access. Use HTTPS or upload the report instead.";
    }

    return isHi ? "कैमरा खोलने में त्रुटि हुई।" : "Unable to open the camera.";
  };

  const openCamera = async () => {
    onActivity();

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
    onActivity();

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

  const handleFileSelection = (event: React.ChangeEvent<HTMLInputElement>) => {
    onActivity();
    setError(null);

    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    if (!file.type.startsWith("image/") && file.type !== "application/pdf") {
      setError(
        isHi
          ? "कृपया JPG, PNG या PDF रिपोर्ट चुनें।"
          : "Please select a JPG, PNG, or PDF report.",
      );

      event.target.value = "";
      return;
    }

    if (file.size > 15 * 1024 * 1024) {
      setError(
        isHi
          ? "रिपोर्ट का आकार 15 MB से कम होना चाहिए।"
          : "The report must be smaller than 15 MB.",
      );

      event.target.value = "";
      return;
    }

    setCapturedFile(file);

    if (file.type.startsWith("image/")) {
      setCapturedImage(URL.createObjectURL(file));
    } else {
      setCapturedImage(null);
    }
  };

  const retakeImage = () => {
    onActivity();

    if (capturedImage) {
      URL.revokeObjectURL(capturedImage);
    }

    setCapturedImage(null);
    setCapturedFile(null);
    setError(null);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const confirmSave = async () => {
    if (!capturedFile || isSaving) {
      return;
    }

    onActivity();
    stopCamera();
    setError(null);
    setIsSaving(true);

    try {
      const document: PatientDraftDocument = await savePatientDraftDocument(
        draftId,
        capturedFile,
        "OTHER",
      );

      if (!document) {
        throw new Error("Unable to save the report locally.");
      }

      setUploadedCount((count) => count + 1);

      if (capturedImage) {
        URL.revokeObjectURL(capturedImage);
      }

      setCapturedImage(null);
      setCapturedFile(null);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (saveError) {
      setError(
        saveError instanceof Error
          ? saveError.message
          : isHi
            ? "रिपोर्ट स्थानीय रूप से सहेजी नहीं जा सकी।"
            : "Unable to save the report locally.",
      );
    } finally {
      setIsSaving(false);
    }
  };

  const handleNext = () => {
    onActivity();
    onNext();
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
            onClick={() => {
              onActivity();
              stopCamera();
            }}
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

  if (capturedFile) {
    return (
      <div className="flex min-h-[80vh] w-full flex-col items-center justify-center bg-bg px-4">
        <div className="mb-6 space-y-4 text-center">
          <h2 className="text-3xl font-bold text-text-primary">
            {isHi ? "रिपोर्ट तैयार है" : "Report Ready"}
          </h2>

          <p className="text-xl text-text-secondary">
            {isHi
              ? "रिपोर्ट सेव करने से पहले जांच लें"
              : "Review the report before saving"}
          </p>
        </div>

        {capturedImage ? (
          <div className="mb-8 rounded-2xl border-2 border-border bg-surface p-6 shadow-lg">
            <img
              src={capturedImage}
              alt="Selected document"
              className="max-h-96 max-w-2xl rounded-lg object-contain"
            />
          </div>
        ) : (
          <div className="mb-8 flex min-h-48 min-w-80 flex-col items-center justify-center rounded-2xl border-2 border-border bg-surface p-8 shadow-lg">
            <FileUp className="mb-4 h-12 w-12 text-primary-dark" />
            <p className="text-lg font-semibold text-text-primary">
              {capturedFile.name}
            </p>
            <p className="mt-2 text-sm text-text-secondary">
              {(capturedFile.size / (1024 * 1024)).toFixed(2)} MB
            </p>
          </div>
        )}

        {error && (
          <div className="mb-5 rounded-xl border-2 border-danger bg-surface px-6 py-3 text-center text-sm font-semibold text-danger">
            {error}
          </div>
        )}

        <div className="flex gap-6">
          <Button
            className="flex items-center gap-3 rounded-xl border-2 border-border px-8 py-6 text-xl text-text-secondary hover:bg-surface-alt"
            disabled={isSaving}
            onClick={retakeImage}
            variant="outline"
          >
            <RotateCcw className="h-6 w-6" />
            {isHi ? "फिर से चुनें" : "Choose Again"}
          </Button>

          <Button
            className="flex items-center gap-3 rounded-xl bg-primary-dark px-10 py-6 text-xl text-white shadow-lg transition-all hover:bg-text-primary"
            disabled={isSaving}
            onClick={() => {
              void confirmSave();
            }}
          >
            {isSaving ? (
              <Loader2 className="h-6 w-6 animate-spin" />
            ) : (
              <Check className="h-6 w-6" />
            )}

            {isSaving
              ? isHi
                ? "सहेजा जा रहा है..."
                : "Saving..."
              : isHi
                ? "स्थानीय रूप से सहेजें"
                : "Save Locally"}
          </Button>
        </div>
      </div>
    );
  }

  const hasSavedDocuments = uploadedCount > 0;

  return (
    <div className="flex min-h-[80vh] w-full flex-col items-center justify-center bg-bg px-4">
      <div className="mb-10 space-y-4 text-center">
        <div className="mb-6 flex justify-center">
          <div className="flex h-24 w-24 items-center justify-center rounded-full bg-primary-tint">
            <Camera className="h-12 w-12 text-primary-dark" />
          </div>
        </div>

        <h2 className="text-4xl font-bold text-text-primary">
          {hasSavedDocuments
            ? isHi
              ? "एक और रिपोर्ट जोड़ें"
              : "Add Another Report"
            : isHi
              ? "रिपोर्ट जोड़ें"
              : "Add Your Report"}
        </h2>

        <p className="mx-auto max-w-xl text-xl text-text-secondary">
          {hasSavedDocuments
            ? isHi
              ? "आप चाहें तो और रिपोर्ट या प्रिस्क्रिप्शन जोड़ सकते हैं"
              : "You can add more reports or prescriptions if needed"
            : isHi
              ? "कैमरे से स्कैन करें या अपने डिवाइस से रिपोर्ट चुनें"
              : "Scan with your camera or choose a report from your device"}
        </p>
      </div>

      {error && (
        <div className="mb-6 max-w-2xl rounded-xl border-2 border-danger bg-surface px-6 py-3 text-center text-sm font-semibold text-danger">
          {error}
        </div>
      )}

      {hasSavedDocuments && (
        <div className="mb-6 rounded-xl border-2 border-border bg-surface px-6 py-3 text-center text-sm font-semibold text-text-secondary">
          {isHi
            ? `${uploadedCount} रिपोर्ट स्थानीय रूप से सहेजी गई`
            : `${uploadedCount} report${uploadedCount === 1 ? "" : "s"} saved locally`}
        </div>
      )}

      <input
        ref={fileInputRef}
        accept="image/*,.pdf"
        className="hidden"
        onChange={handleFileSelection}
        type="file"
      />

      <div className="flex w-full max-w-2xl flex-col gap-5 sm:flex-row">
        <Button
          className="flex flex-1 items-center justify-center gap-4 rounded-2xl bg-primary-dark px-8 py-7 text-xl text-white shadow-xl transition-all hover:bg-text-primary"
          onClick={() => {
            void openCamera();
          }}
        >
          <Camera className="h-7 w-7" />
          {isHi ? "कैमरा खोलें" : "Open Camera"}
        </Button>

        <Button
          className="flex flex-1 items-center justify-center gap-4 rounded-2xl border-2 border-border px-8 py-7 text-xl text-text-secondary hover:bg-surface-alt"
          onClick={() => {
            onActivity();
            setError(null);
            fileInputRef.current?.click();
          }}
          variant="outline"
        >
          <FileUp className="h-7 w-7" />
          {isHi ? "रिपोर्ट चुनें" : "Upload Report"}
        </Button>
      </div>

      <Button
        className="mt-6 rounded-xl border-2 border-border px-8 py-4 text-lg text-text-secondary hover:bg-surface-alt"
        onClick={handleNext}
        variant="outline"
      >
        {hasSavedDocuments
          ? isHi
            ? "जारी रखें"
            : "Continue"
          : isHi
            ? "छोड़ दें"
            : "Skip This Step"}
      </Button>

      <p className="mt-8 text-center text-lg text-text-secondary">
        {isHi
          ? "JPG, PNG या PDF का उपयोग कर सकते हैं"
          : "You can use JPG, PNG, or PDF files"}
      </p>
    </div>
  );
}
