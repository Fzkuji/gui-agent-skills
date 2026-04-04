"""
gui_harness.primitives.detector — GPA-GUI-Detector and merged detection.

Thin wrapper around the detection parts of scripts/ui_detector.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = str(Path(__file__).parent.parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)


def detect_icons(img_path: str, conf: float = 0.1, iou: float = 0.3) -> tuple[list[dict], int, int]:
    """Detect UI elements using GPA-GUI-Detector (YOLO).

    Returns:
        (elements, img_w, img_h)
    """
    from ui_detector import detect_icons as _detect_icons
    return _detect_icons(img_path, conf=conf, iou=iou)


def detect_all(img_path: str, conf: float = 0.1, iou: float = 0.3) -> tuple:
    """Unified detection: GPA + OCR + merge + coordinate conversion.

    Returns:
        (icons, texts, merged, img_w, img_h) — merged in click-space coordinates.
    """
    from ui_detector import detect_all as _detect_all
    return _detect_all(img_path, conf=conf, iou=iou)


def get_screen_info() -> dict:
    """Return current screen scale info."""
    from ui_detector import get_screen_info as _get_info
    return _get_info()
