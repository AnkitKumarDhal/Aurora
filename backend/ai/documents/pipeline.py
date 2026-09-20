from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from backend.ai.documents.discharge import extract_discharge_summary
from backend.ai.documents.extractor import extract_document
from backend.ai.documents.laboratory import extract_lab_report
from backend.ai.ocr.engine import ocr_document


def process_medical_document(image_path: str) -> dict[str, Any]:
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

    if document_type == "lab_report":
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


def print_result(result: dict[str, Any]) -> None:
    print("=" * 70)
    print("AURORA MEDICAL DOCUMENT PIPELINE")
    print("=" * 70)
    print()
    print("OCR status:", result.get("ocr", {}).get("status"))
    print("Document type:", result.get("ocr", {}).get("document_type"))
    print("OCR confidence:", result.get("ocr", {}).get("mean_confidence"))
    print()
    print(result.get("ocr", {}).get("text"))
    print()
    print(
        json.dumps(
            result.get("structured_document"),
            indent=2,
            ensure_ascii=False,
        )
    )
    print()
    print("Overall status:", result.get("status"))
    print("Image:", result.get("image_path"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Process a medical document image through Aurora.",
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
