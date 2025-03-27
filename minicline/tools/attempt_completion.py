"""Tool for executing system commands."""

import subprocess
from typing import Tuple, Dict, Any
from pathlib import Path

def attempt_completion(result: str, auto: bool) -> Tuple[str, str]:
    """Attempt to complete a task

    Args:
        result: The result text from the AI
        auto: Whether to automatically approve the action

    Returns:
        Tuple of (tool_call_summary, result_text) where:
        - tool_call_summary is a string describing the tool call
        - result_text contains the command output or error message
    """
    tool_call_summary = f"attempt_completion"

    print(result)

    if not auto:
        question = f"Press ENTER or 'y' to complete task or enter a message to reject this action [y]"
        response = input(f"{question}: ").strip()
        if response.lower() not in ["", "y"]:
            return tool_call_summary, f"User rejected completing the task with the following message: {response}"

    # TASK_COMPLETE is a special string that triggers completion
    return tool_call_summary, "TASK_COMPLETE"
