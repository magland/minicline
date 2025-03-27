"""Tool for executing system commands."""

import subprocess
from typing import Tuple, Dict, Any
from pathlib import Path

def execute_command(command: str, requires_approval: bool, *, cwd: str) -> Tuple[str, str]:
    """Execute a system command.

    Args:
        command: The command to execute
        requires_approval: Whether the command requires explicit user approval
        cwd: Current working directory

    Returns:
        Tuple of (tool_call_summary, result_text) where:
        - tool_call_summary is a string describing the tool call
        - result_text contains the command output or error message
    """
    tool_call_summary = f"execute_command '{command}'"
    if requires_approval:
        tool_call_summary += " (requires approval)"

    print("================================")
    print("Command to be executed")
    print(command)
    print("================================")

    question = f"Would you like to execute the above command? Press ENTER or 'y' to execute the command or enter a message to reject this action [y]"
    response = input(f"{question}: ").strip()
    if response.lower() not in ["", "y"]:
        return tool_call_summary, f"User rejected executing the command with the following message: {response}"

    # For now we always ask for approval... in the future we can respect the requires_approval flag
    # # if requires approval, ask user to approve by typing 'yes' or 'y'
    # if requires_approval:
    #     print(f"Approval required to execute command: {command}")
    #     user_approval = input("Type 'yes' or 'y' to approve: ")
    #     if user_approval.lower() not in ["yes", "y"]:
    #         return tool_call_summary, "Command execution not approved by user"

    try:
        # Run command and capture output
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            text=True,
            capture_output=True
        )

        # Format output including both stdout and stderr
        output_parts = []
        if result.stdout:
            output_parts.append(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            output_parts.append(f"STDERR:\n{result.stderr}")

        if result.returncode == 0:
            output_parts.insert(0, "Command executed successfully")
        else:
            output_parts.insert(0, f"Command failed with exit code {result.returncode}")

        return tool_call_summary, "\n".join(output_parts)

    except Exception as e:
        return tool_call_summary, f"ERROR executing command: {str(e)}"
