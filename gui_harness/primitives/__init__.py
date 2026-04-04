"""
gui_harness.primitives — pure Python tools (no @agentic_function decorator).

Thin wrappers around the original scripts/ modules.
"""

from gui_harness.primitives import screenshot, ocr, detector, template_match
from gui_harness.primitives import input as gui_input

__all__ = ["screenshot", "ocr", "detector", "gui_input", "template_match"]
