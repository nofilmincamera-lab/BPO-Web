#!/usr/bin/env python3
"""Wrapper so `python /app/preprocess_ocr.py ...` works inside containers."""
from scripts.preprocess_ocr import main


if __name__ == "__main__":
    raise SystemExit(main())
