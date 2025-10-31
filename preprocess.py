#!/usr/bin/env python3
"""
Wrapper script so containers/automation can invoke the canonical
`scripts.preprocess` module via `python /app/preprocess.py ...`.

Historically these helpers were called with positional arguments
(`python preprocess.py /path/to/input /path/to/output`).  The upstream
`scripts.preprocess` CLI expects `--input/--output` flags, so we translate
legacy positional usage into the modern form here.  When a directory is
provided we pick the first `.jsonl` file and emit results to
`preprocessed.jsonl` under the supplied output directory.
"""
from __future__ import annotations

from pathlib import Path
import sys
from typing import List

from scripts.preprocess import main


def _translate_legacy_invocation(argv: List[str]) -> List[str]:
    """Shim positional `input output` arguments into flag-based CLI."""
    if len(argv) < 3 or argv[1].startswith("-"):
        return argv

    input_arg = Path(argv[1])
    output_arg = Path(argv[2])
    rest = argv[3:]

    resolved_input = input_arg
    if input_arg.is_dir():
        candidates = sorted(input_arg.glob("*.jsonl"))
        if not candidates:
            raise SystemExit(
                f"No .jsonl files found in input directory: {input_arg}"
            )
        resolved_input = candidates[0]

    resolved_output = output_arg
    if output_arg.is_dir() or output_arg.suffix == "":
        resolved_output = output_arg / "preprocessed.jsonl"

    return [
        argv[0],
        "--input",
        str(resolved_input),
        "--output",
        str(resolved_output),
        *rest,
    ]


if __name__ == "__main__":
    sys.argv = _translate_legacy_invocation(sys.argv)
    raise SystemExit(main())
