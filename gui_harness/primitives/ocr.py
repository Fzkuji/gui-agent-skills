"""
gui_harness.primitives.ocr — Apple Vision OCR.

Thin wrapper around the OCR parts of scripts/ui_detector.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = str(Path(__file__).parent.parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)


def detect_text(img_path: str, return_logical: bool = False) -> list[dict]:
    """Detect text using Apple Vision OCR.

    Args:
        img_path: Path to screenshot image.
        return_logical: If True, return coordinates in logical (click) space.

    Returns:
        List of dicts with keys: type, source, x, y, w, h, cx, cy, confidence, label
    """
    from ui_detector import detect_text as _detect_text
    return _detect_text(img_path, return_logical=return_logical)
