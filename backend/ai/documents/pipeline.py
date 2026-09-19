from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from document_ocr import ocr_document
from document_extractor import extract_document
from lab_document_extractor import extract_lab_report
from discharge_document_extractor import extract_discharge_summary


def process_medical_document(image_path: str) -> Dict[str, Any]:
    """
    Main MediKiosk medical-document pipeline.

    Image
        -> OCR
        -> document classification
        -> appropriate structured extractor
    """

    image_path = str(Path(image_path).resolve())

    ocr = ocr_document(image_path)

    if ocr.get("status") != "success":
        return {
            "status": "failed",
            "stage": "ocr",
            "image_path": image_path,
            "ocr": ocr,
        }

    document_type = str(
        ocr.get("document_type") or "unknown"
    ).lower()

    if document_type == "prescription":
        structured = extract_document(ocr)

    elif document_type == "lab_report":
        structured = extract_lab_report(ocr)

    elif document_type == "discharge_summary":
        structured = extract_discharge_summary(ocr)

    else:
        structured = extract_document(ocr)

    return {
        "status": structured.get("status", "success"),
        "image_path": image_path,
        "ocr": ocr,
        "structured_document": structured,
    }


def print_result(result: Dict[str, Any]) -> None:
    print("=" * 70)
    print("             MEDIKIOSK MEDICAL DOCUMENT PIPELINE")
    print("=" * 70)

    print("\n========== OCR ==========")

    ocr = result.get("ocr", {})

    print("Status:", ocr.get("status"))
    print("Document type:", ocr.get("document_type"))
    print("Confidence:", ocr.get("mean_confidence"))
    print("Raw text:")
    print(ocr.get("text"))

    print("\n========== STRUCTURED DOCUMENT ==========")

    print(
        json.dumps(
            result.get("structured_document"),
            indent=2,
            ensure_ascii=False,
        )
    )

    print("\n========== PIPELINE RESULT ==========")

    print("Overall status:", result.get("status"))
    print("Image:", result.get("image_path"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Process a medical document image through MediKiosk."
    )

    parser.add_argument(
        "image",
        help="Path to medical document image",
    )

    args = parser.parse_args()

    result = process_medical_document(args.image)

    print_result(result)

    if result.get("status") != "success":
        raise SystemExit(1)


if __name__ == "__main__":
    main()