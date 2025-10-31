#!/usr/bin/env python3
"""
Label Studio OCR preprocessing helper.

Scans an input directory for PDF/image/text files, extracts text where
possible, and emits both plain-text copies and a JSONL manifest that
Label Studio can import.
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path
from typing import Iterable

from pdfminer.high_level import extract_text as extract_pdf_text

try:
    from PIL import Image
except ImportError:  # pragma: no cover - handled at runtime
    Image = None  # type: ignore

try:
    import pytesseract
except ImportError:  # pragma: no cover - handled at runtime
    pytesseract = None  # type: ignore


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
PDF_EXTENSIONS = {".pdf"}
TEXT_EXTENSIONS = {".txt", ".md"}


def iter_files(input_dir: Path) -> Iterable[Path]:
    for path in sorted(input_dir.rglob("*")):
        if path.is_file():
            yield path


def extract_text(path: Path, lang: str) -> str:
    suffix = path.suffix.lower()

    if suffix in PDF_EXTENSIONS:
        return extract_pdf_text(str(path))

    if suffix in IMAGE_EXTENSIONS:
        if Image is None or pytesseract is None:
            raise RuntimeError(
                "Image OCR requested but Pillow/pytesseract are not installed."
            )
        with Image.open(path) as img:
            return pytesseract.image_to_string(img, lang=lang)

    if suffix in TEXT_EXTENSIONS:
        return path.read_text(encoding="utf-8", errors="ignore")

    # Fallback: treat as binary/text blob
    return path.read_text(encoding="utf-8", errors="ignore")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate Label Studio-ready OCR tasks from documents."
    )
    parser.add_argument("input_dir", type=Path, help="Directory with source documents.")
    parser.add_argument("output_dir", type=Path, help="Directory to store artifacts.")
    parser.add_argument(
        "--lang",
        default="eng",
        help="Tesseract language code (default: eng).",
    )
    parser.add_argument(
        "--manifest-name",
        default="ocr_tasks.jsonl",
        help="Name of the JSONL manifest file (default: ocr_tasks.jsonl).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    input_dir: Path = args.input_dir
    output_dir: Path = args.output_dir
    manifest_path = output_dir / args.manifest_name

    if not input_dir.exists():
        parser.error(f"Input directory not found: {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    processed = 0
    skipped = 0
    with manifest_path.open("w", encoding="utf-8") as manifest:
        for file_path in iter_files(input_dir):
            suffix = file_path.suffix.lower()
            if suffix not in IMAGE_EXTENSIONS | PDF_EXTENSIONS | TEXT_EXTENSIONS:
                skipped += 1
                continue

            try:
                text = extract_text(file_path, lang=args.lang).strip()
            except Exception as exc:  # pragma: no cover - runtime warnings
                print(f"[WARN] Failed to process {file_path}: {exc}", file=sys.stderr)
                skipped += 1
                continue

            if not text:
                skipped += 1
                continue

            text_filename = f"{file_path.stem}_{uuid.uuid4().hex}.txt"
            text_path = output_dir / text_filename
            text_path.write_text(text, encoding="utf-8")

            task = {
                "id": str(uuid.uuid4()),
                "data": {
                    "text_path": str(text_path),
                    "source_path": str(file_path),
                },
            }
            manifest.write(json.dumps(task, ensure_ascii=False) + "\n")
            processed += 1

    print(f"[INFO] Processed {processed} documents (skipped {skipped}).")
    print(f"[INFO] Manifest written to {manifest_path}")
    return 0 if processed else 1


if __name__ == "__main__":
    raise SystemExit(main())
