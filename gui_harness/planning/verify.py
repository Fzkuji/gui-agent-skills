"""
verify — check if an action achieved the expected result.

Session mode: summarize={"depth": 0, "siblings": 0}
"""

from __future__ import annotations

import json

from agentic import agentic_function
from gui_harness.perception import screenshot, ocr

_runtime = None


def _get_runtime():
    global _runtime
    if _runtime is None:
        from gui_harness.runtime import GUIRuntime
        _runtime = GUIRuntime()
    return _runtime


@agentic_function(summarize={"depth": 0, "siblings": 0})
def verify(expected: str, runtime=None) -> dict:
    """Verify whether a previous action produced the expected result.

    You will receive a screenshot and OCR text of the current screen.
    Determine if the expected outcome is visible.

    Provide specific evidence: quote the exact text or element that
    confirms or denies the expectation.

    Return JSON:
    {
      "expected": "...",
      "actual": "what you actually see on screen",
      "verified": true/false,
      "evidence": "specific text or element that confirms/denies",
      "screenshot_path": "..."
    }
    """
    rt = runtime or _get_runtime()

    img_path = screenshot.take()
    ocr_results = ocr.detect_text(img_path)
    ocr_lines = "\n".join(
        f"  '{el.get('label', '')}'" for el in ocr_results[:40]
    )

    context = f"""Expected: {expected}

OCR text on screen:
{ocr_lines or '(none)'}"""

    reply = rt.exec(content=[
        {"type": "text", "text": context},
        {"type": "image", "path": img_path},
    ])

    try:
        result = _parse_json(reply)
        result.setdefault("screenshot_path", img_path)
    except Exception:
        result = {
            "expected": expected, "actual": reply[:300],
            "verified": False, "evidence": "Failed to parse LLM response",
            "screenshot_path": img_path,
        }
    return result


def _parse_json(reply: str) -> dict:
    text = reply.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    return json.loads(text)
