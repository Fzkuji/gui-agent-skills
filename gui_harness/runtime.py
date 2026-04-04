"""
gui_harness.runtime — GUIRuntime: GUI-optimized LLM runtime.

GUIRuntime extends AnthropicRuntime with sensible defaults for GUI automation:
  - System prompt tailored for GUI tasks
  - Default model: claude-sonnet-4-20250514
  - Image content block support (already in AnthropicRuntime)

Usage:
    from gui_harness.runtime import GUIRuntime

    runtime = GUIRuntime()

    @agentic_function
    def observe(task):
        ...
        return runtime.exec(content=[...])
"""

from __future__ import annotations

from agentic.providers.anthropic import AnthropicRuntime

GUI_SYSTEM_PROMPT = """\
You are a GUI automation agent operating on a macOS desktop.

Your role:
- Analyze screenshots, OCR results, and detected UI elements
- Identify the target elements and their exact pixel coordinates
- Decide the best actions to achieve the given task
- Return structured JSON responses as requested

Rules:
- ALWAYS use coordinates from OCR/detector output — never estimate from visual inspection
- Be precise: wrong coordinates break automation
- When in doubt about element identity, use the OCR text as ground truth
- Report exactly what you see; do not hallucinate UI elements
"""


class GUIRuntime(AnthropicRuntime):
    """
    GUI-optimized Anthropic runtime.

    Inherits full AnthropicRuntime functionality (image/text blocks, caching, retries).
    Pre-configured with a GUI automation system prompt and a capable vision model.

    Args:
        model:      Claude model name. Defaults to "claude-sonnet-4-20250514".
        system:     System prompt. Defaults to GUI_SYSTEM_PROMPT.
        **kwargs:   Forwarded to AnthropicRuntime (api_key, max_tokens, etc.).
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("system", GUI_SYSTEM_PROMPT)
        kwargs.setdefault("model", "claude-sonnet-4-20250514")
        super().__init__(**kwargs)
