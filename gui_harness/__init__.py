"""
gui_harness — GUI automation powered by Agentic Programming.

Primary entry point: gui_agent() in main.py
Architecture: Phase 0-5 loop (see DESIGN_unified_actions.md)
"""

from gui_harness.constants import GUI_SYSTEM_PROMPT
from gui_harness.tasks.execute_task import execute_task
from gui_harness.main import gui_agent
from gui_harness.planning.component_memory import locate_target

__all__ = [
    "GUI_SYSTEM_PROMPT",
    "gui_agent",
    "execute_task",
    "locate_target",
]
