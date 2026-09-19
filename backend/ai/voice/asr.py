from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

MODEL_NAME = os.getenv("MEDIKIOSK_WHISPER_MODEL", "base")
SUPPORTED_LANGUAGES = {
    "english": "en", "hindi": "hi", "bengali": "bn", "gujarati": "gu", "kannada": "kn",
    "malayalam": "ml", "marathi": "mr", "odia": "or", "oriya": "or", "punjabi": "pa",
    "tamil": "ta", "telugu": "te",
}


def normalise_language(language: Optional[str]) -> Optional[str]:
    if not language:
        return None
    key = language.strip().lower()
    return SUPPORTED_LANGUAGES.get(key, key if len(key) == 2 else None)


def transcribe_audio(audio_path: str, language: Optional[str] = None, model_name: Optional[str] = None) -> Dict[str, Any]:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        return {"status": "failed", "stage": "dependency", "error": "faster-whisper is not installed. Install it with: pip install faster-whisper", "exception": str(exc)}

    path = str(Path(audio_path).resolve())
    if not Path(path).exists():
        return {"status": "failed", "stage": "input", "error": f"Audio file not found: {path}"}

    selected_model = model_name or MODEL_NAME
    selected_language = normalise_language(language)
    try:
        model = WhisperModel(selected_model, device=os.getenv("MEDIKIOSK_WHISPER_DEVICE", "cpu"), compute_type=os.getenv("MEDIKIOSK_WHISPER_COMPUTE", "int8"))
        segments, info = model.transcribe(path, language=selected_language, beam_size=5, vad_filter=True)
        text = " ".join(segment.text.strip() for segment in segments if segment.text.strip())
        return {
            "status": "success", "audio_path": path, "model": selected_model,
            "language_requested": selected_language, "language_detected": getattr(info, "language", None),
            "language_probability": getattr(info, "language_probability", None), "text": text,
        }
    except Exception as exc:
        return {"status": "failed", "stage": "transcription", "error": str(exc), "audio_path": path, "model": selected_model}
