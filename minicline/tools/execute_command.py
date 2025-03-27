"""Tool for executing system commands."""

import subprocess
from typing import Tuple

def execute_command(command: str, requires_approval: bool, *, cwd: str, auto: bool, approve_all_commands: bool, timeout: int = 60) -> Tuple[str, str]:
    """Execute a system command.

    Args:
        command: The command to execute
        requires_approval: Whether the command requires explicit user approval
        cwd: Current working directory
        auto: Whether running in automatic mode
        approve_all_commands: Whether to automatically approve all commands
        timeout: Maximum time in seconds to wait for command completion (default: 60, 0 for no timeout)

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

    ask_user = True
    if approve_all_commands:
        ask_user = False
    if auto and not requires_approval:
        ask_user = False

    if ask_user:
        if requires_approval:
            question = f"Would you like to execute the above command (requires approval)? Press ENTER or 'y' to execute the command or enter a message to reject this action [y]"
        else:
            question = f"Would you like to execute the above command? Press ENTER or 'y' to execute the command or enter a message to reject this action [y]"
        response = input(f"{question}: ").strip()
        if response.lower() not in ["", "y"]:
            return tool_call_summary, f"User rejected executing the command with the following message: {response}"

    try:
        # Run command and capture output
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                text=True,
                capture_output=True,
                timeout=timeout if timeout > 0 else None
            )
        except subprocess.TimeoutExpired:
            return tool_call_summary, f"Command timed out after {timeout} seconds"

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
