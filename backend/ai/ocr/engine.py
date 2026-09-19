from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import pytesseract
from PIL import Image


DEFAULT_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]


def _configure_tesseract() -> str:
    configured = os.getenv("TESSERACT_CMD")
    if configured and Path(configured).exists():
        pytesseract.pytesseract.tesseract_cmd = configured
        return configured

    for candidate in DEFAULT_TESSERACT_PATHS:
        if Path(candidate).exists():
            pytesseract.pytesseract.tesseract_cmd = candidate
            return candidate

    found = shutil.which("tesseract")
    if found:
        pytesseract.pytesseract.tesseract_cmd = found
        return found

    return "tesseract"


def _load_image(image_path: str) -> np.ndarray:
    image = cv2.imread(image_path)

    if image is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")

    return image


def _auto_crop_document(image: np.ndarray) -> np.ndarray:
    """
    Remove large empty margins around the actual document text/content.

    This matters for photographed/scanned documents where text may occupy
    only a small portion of a large image. Tesseract performs much better
    when characters are represented at a useful scale.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Identify pixels that are meaningfully darker than a white background.
    mask = cv2.threshold(gray, 245, 255, cv2.THRESH_BINARY_INV)[1]

    # Connect nearby letters/lines without aggressively merging everything.
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

    points = cv2.findNonZero(mask)

    if points is None:
        return image

    x, y, w, h = cv2.boundingRect(points)

    image_h, image_w = gray.shape[:2]
    area_ratio = (w * h) / float(image_w * image_h)

    # Don't crop normal full-frame documents.
    if area_ratio > 0.88:
        return image

    # Add generous padding so document headings and neighboring text remain.
    pad_x = max(30, int(w * 0.08))
    pad_y = max(30, int(h * 0.08))

    x1 = max(0, x - pad_x)
    y1 = max(0, y - pad_y)
    x2 = min(image_w, x + w + pad_x)
    y2 = min(image_h, y + h + pad_y)

    return image[y1:y2, x1:x2]


def _prepare_for_ocr(image: np.ndarray) -> np.ndarray:
    cropped = _auto_crop_document(image)

    gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)

    # Make characters large enough for reliable recognition.
    height, width = gray.shape[:2]
    target_width = 2200

    if width < target_width:
        scale = target_width / float(width)
        gray = cv2.resize(
            gray,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv2.INTER_CUBIC,
        )

    # Mild denoising.
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    # Otsu gives a clean black-on-white document image.
    _, binary = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )

    return binary


def _safe_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _document_type(text: str) -> str:
    t = text.lower()

    prescription_terms = [
        "rx",
        "prescription",
        "tablet",
        "capsule",
        "syrup",
        "dose",
        "dosage",
        "mg",
        "ml",
        "od",
        "bd",
        "tid",
        "before food",
        "after food",
    ]

    lab_terms = [
        "laboratory",
        "lab report",
        "hemoglobin",
        "haemoglobin",
        "wbc",
        "rbc",
        "platelet",
        "glucose",
        "creatinine",
        "reference range",
        "test result",
        "patient id",
    ]

    discharge_terms = [
        "discharge summary",
        "discharged",
        "admission",
        "discharge diagnosis",
        "hospital course",
        "follow-up",
        "follow up",
    ]

    scores = {
        "prescription": sum(term in t for term in prescription_terms),
        "lab_report": sum(term in t for term in lab_terms),
        "discharge_summary": sum(term in t for term in discharge_terms),
    }

    best_type = max(scores, key=scores.get)
    return best_type if scores[best_type] > 0 else "unknown"


def _run_ocr(
    processed: np.ndarray,
    language: str,
    timeout_seconds: float,
) -> Tuple[str, float, int]:
    data = pytesseract.image_to_data(
        Image.fromarray(processed),
        lang=language,
        config="--oem 3 --psm 6",
        output_type=pytesseract.Output.DICT,
        timeout=timeout_seconds,
    )

    words: List[str] = []
    confidences: List[float] = []

    for text, confidence in zip(
        data.get("text", []),
        data.get("conf", []),
    ):
        clean = str(text).strip()
        conf = _safe_float(confidence)

        if clean:
            words.append(clean)

        if clean and conf is not None and conf >= 0:
            confidences.append(conf)

    raw_text = " ".join(words).strip()

    mean_confidence = (
        round(sum(confidences) / len(confidences), 2)
        if confidences
        else 0.0
    )

    return raw_text, mean_confidence, len(words)


def ocr_document(
    image_path: str,
    lang: Optional[str] = None,
    timeout_seconds: float = 12.0,
) -> Dict[str, Any]:
    image_path = str(Path(image_path).resolve())

    if not Path(image_path).exists():
        raise FileNotFoundError(f"Document image not found: {image_path}")

    tess_cmd = _configure_tesseract()
    language = lang or os.getenv("MEDIKIOSK_OCR_LANG", "eng")

    try:
        image = _load_image(image_path)
        processed = _prepare_for_ocr(image)

        raw_text, mean_confidence, word_count = _run_ocr(
            processed,
            language,
            timeout_seconds,
        )

    except RuntimeError as exc:
        return {
            "status": "failed",
            "error": f"OCR timed out: {exc}",
            "image_path": image_path,
            "tesseract_cmd": tess_cmd,
        }

    except pytesseract.TesseractNotFoundError:
        return {
            "status": "failed",
            "error": (
                "Tesseract executable was not found. "
                "Install Tesseract OCR and/or set TESSERACT_CMD."
            ),
            "image_path": image_path,
            "tesseract_cmd": tess_cmd,
        }

    possible_low_quality = (
        mean_confidence < 55.0
        or word_count < 4
        or len(raw_text.strip()) < 20
    )

    review_reasons: List[str] = []

    if possible_low_quality:
        review_reasons.append(
            "OCR confidence is low or very little text was extracted. "
            "The image may contain handwriting, blur, poor lighting, "
            "or an unsupported layout."
        )

    if not raw_text:
        review_reasons.append("No readable text was extracted.")

    return {
        "status": "success",
        "image_path": image_path,
        "tesseract_cmd": tess_cmd,
        "language": language,
        "text": raw_text,
        "mean_confidence": mean_confidence,
        "word_count": word_count,
        "document_type": _document_type(raw_text),
        "possible_handwriting_or_low_quality": possible_low_quality,
        "manual_review_required": bool(review_reasons),
        "review_reasons": review_reasons,
    }
