"""
learn — learn an app's UI by labeling detected components.

Session mode: summarize={"depth": 0, "siblings": 0}
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from agentic import agentic_function
from gui_harness.perception import screenshot, ocr, detector

_runtime = None


def _get_runtime():
    global _runtime
    if _runtime is None:
        from gui_harness.runtime import GUIRuntime
        _runtime = GUIRuntime()
    return _runtime


@agentic_function(summarize={"depth": 0, "siblings": 0})
def learn(app_name: str, runtime=None) -> dict:
    """Learn the UI of an app by labeling its components.

    You will receive detected UI components and OCR text from a screenshot.
    For each interactive component:
    1. Assign a descriptive snake_case name (e.g., search_bar, send_button)
    2. Skip purely decorative or background elements
    3. Identify the current page name

    Return JSON:
    {
      "app_name": "...",
      "page_name": "current_page_name",
      "component_names": ["search_bar", "send_button", ...],
      "components_found": <total count>,
      "components_saved": 0,
      "already_known": false
    }
    """
    rt = runtime or _get_runtime()

    img_path = screenshot.take()
    ocr_results = ocr.detect_text(img_path)

    try:
        _, _, elements, _, _ = detector.detect_all(img_path)
    except Exception:
        elements = ocr_results

    det_lines = "\n".join(
        f"  Component {i}: at ({el.get('cx', 0)}, {el.get('cy', 0)}) "
        f"size={el.get('w', 0)}x{el.get('h', 0)} label={el.get('label') or 'unknown'}"
        for i, el in enumerate(elements[:50])
    )
    ocr_lines = "\n".join(
        f"  '{el.get('label', '')}' at ({el.get('cx', 0)}, {el.get('cy', 0)})"
        for el in ocr_results[:60]
    )

    context = f"""App: {app_name}

Detected components:
{det_lines or '(none)'}

OCR text:
{ocr_lines or '(none)'}"""

    reply = rt.exec(content=[
        {"type": "text", "text": context},
        {"type": "image", "path": img_path},
    ])

    try:
        result = _parse_json(reply)
        result.setdefault("app_name", app_name)
        result.setdefault("components_found", len(elements))

        # Save to app_memory if available
        try:
            scripts_dir = str(Path(__file__).parent.parent.parent / "scripts")
            if scripts_dir not in sys.path:
                sys.path.insert(0, scripts_dir)
            from app_memory import learn_from_screenshot
            saved = learn_from_screenshot(img_path, app_name, result.get("page_name", "unknown"))
            result["components_saved"] = saved.get("saved", 0)
        except Exception:
            pass
    except Exception:
        result = {
            "app_name": app_name, "page_name": "unknown",
            "component_names": [], "components_found": len(elements),
            "components_saved": 0, "already_known": False,
        }

    return result


def _parse_json(reply: str) -> dict:
    text = reply.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    return json.loads(text)
