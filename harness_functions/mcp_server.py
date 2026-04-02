#!/usr/bin/env python3
"""
MCP Server for Agentic Functions.

Registers all GUI Agent functions as MCP tools so that any MCP client
(Claude Code, Codex, OpenClaw, etc.) can call them directly.

Usage:
    python3 mcp_server.py

    Then in Claude Code's .mcp.json:
    {
        "mcpServers": {
            "gui-agent": {
                "command": "python3",
                "args": ["/path/to/mcp_server.py"]
            }
        }
    }
"""

import sys
from pathlib import Path

# Setup paths
SKILL_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# harness is bundled in-repo (no external dependency)
_harness_path = str(SKILL_DIR)
if _harness_path not in sys.path:
    sys.path.insert(0, _harness_path)

sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("gui-agent", instructions="""
You are an Agentic Programmer for GUI desktop automation.
You have access to Agentic Functions that observe, learn, act on, and verify screen states.
Each function uses Python Runtime (OCR, detection, clicking) + Agentic Runtime (LLM reasoning) together.
""")


# ═══════════════════════════════════════════
# High-level Agentic Functions (LLM + Python)
# ═══════════════════════════════════════════

@mcp.tool()
def observe(task: str, app_name: str = None) -> dict:
    """Observe the current screen state.

    Takes a screenshot, runs OCR + GPA-GUI-Detector, checks visual memory,
    then uses LLM to interpret everything and report what's visible.

    Args:
        task: What to look for (e.g. "find the login button")
        app_name: Override frontmost app detection
    """
    from functions import observe as _observe, _create_worker
    worker = _create_worker()
    result = _observe(None, task=task, app_name=app_name, worker_model="sonnet")
    return result.model_dump()


@mcp.tool()
def learn(app_name: str) -> dict:
    """Learn a new app's UI components.

    Detects all UI elements, has LLM label them, saves to visual memory.
    Run this before operating any app not yet in memory.

    Args:
        app_name: Name of the app to learn
    """
    from functions import learn as _learn
    result = _learn(None, app_name=app_name)
    return result.model_dump()


@mcp.tool()
def act(action: str, target: str, text: str = None, app_name: str = None) -> dict:
    """Perform a GUI action on the screen.

    Detects target via OCR/template match, LLM confirms coordinates,
    then Python executes the click/type, and verifies with before/after diff.

    Args:
        action: "click", "double_click", "right_click", "type"
        target: What to interact with (e.g. "login button", "search bar")
        text: Text to type (for "type" action)
        app_name: Override app detection
    """
    from functions import act as _act
    result = _act(None, action=action, target=target, text=text, app_name=app_name)
    return result.model_dump()


@mcp.tool()
def verify(expected: str) -> dict:
    """Verify whether a previous action succeeded.

    Takes a screenshot, runs OCR, has LLM judge if the expected outcome
    is visible on screen.

    Args:
        expected: What we expect to see (e.g. "login page loaded")
    """
    from functions import verify as _verify
    result = _verify(None, expected=expected)
    return result.model_dump()


@mcp.tool()
def navigate(target_state: str, app_name: str) -> dict:
    """Navigate through an app to reach a target state.

    Uses the state graph from visual memory to find a path,
    then executes each step with act() and verifies transitions.

    Args:
        target_state: The state to reach (e.g. "chat_main", "settings")
        app_name: App to navigate in
    """
    from functions import navigate as _navigate
    result = _navigate(None, target_state=target_state, app_name=app_name)
    return result.model_dump()


@mcp.tool()
def remember(operation: str, app_name: str) -> dict:
    """Manage visual memory for an app.

    Args:
        operation: "list" (show components/states), "forget" (remove stale),
                   "merge" (combine similar states)
        app_name: App to manage memory for
    """
    from functions import remember as _remember
    result = _remember(None, operation=operation, app_name=app_name)
    return result.model_dump()


# ═══════════════════════════════════════════
# Low-level functions (Python only, no LLM)
# ═══════════════════════════════════════════

@mcp.tool()
def screenshot(app_name: str = None) -> dict:
    """Take a screenshot of the current screen.

    Args:
        app_name: Capture specific app window (None = full screen)
    """
    from functions import take_screenshot
    result = take_screenshot(app_name=app_name)
    return result.model_dump()


@mcp.tool()
def ocr(image_path: str) -> dict:
    """Run OCR on an image. Returns text elements with coordinates.

    Args:
        image_path: Path to the image file
    """
    from functions import run_ocr
    result = run_ocr(image_path)
    return result.model_dump()


@mcp.tool()
def detect(image_path: str) -> dict:
    """Run full detection (OCR + GPA-GUI-Detector) on an image.

    Args:
        image_path: Path to the image file
    """
    from functions import detect_all
    result = detect_all(image_path)
    return result.model_dump()


@mcp.tool()
def click_at(x: int, y: int, button: str = "left", clicks: int = 1) -> str:
    """Click at screen coordinates.

    Args:
        x: X coordinate (click-space)
        y: Y coordinate (click-space)
        button: "left", "right", or "middle"
        clicks: Number of clicks (1=single, 2=double)
    """
    from functions import click
    click(x, y, button=button, clicks=clicks)
    return f"Clicked ({x}, {y}) button={button} clicks={clicks}"


@mcp.tool()
def type_text(text: str) -> str:
    """Type text using keyboard.

    Args:
        text: Text to type
    """
    from functions import paste
    paste(text)
    return f"Typed: {text}"


@mcp.tool()
def get_state(app_name: str) -> dict:
    """Identify the current state of an app from visual memory.

    Args:
        app_name: App to check
    """
    from functions import identify_state
    result = identify_state(app_name)
    return result.model_dump()


if __name__ == "__main__":
    mcp.run()
