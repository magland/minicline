"""Tool for executing scripts by writing them to a temporary file and then running them."""

import os
import tempfile
from typing import Tuple

from .execute_command import execute_command

def execute_script(script: str, language: str, requires_approval: bool, *, cwd: str, auto: bool, approve_all_commands: bool, no_container: bool, docker_container: str | None = None) -> Tuple[str, str]:
    """Execute a script by writing it to a temporary file and running it.

    Args:
        script: The script content to execute
        language: The script language (currently only 'python' is supported)
        requires_approval: Whether the script execution requires explicit user approval
        cwd: Current working directory
        auto: Whether running in automatic mode
        approve_all_commands: Whether to automatically approve all commands
        no_container: Whether to run without a container

    Returns:
        Tuple of (tool_call_summary, result_text) where:
        - tool_call_summary is a string describing the tool call
        - result_text contains the execution output or error message
    """
    if language.lower() != "python":
        return f"execute_script (unsupported language: {language})", f"ERROR: Only Python language is currently supported"

    tool_call_summary = f"execute_script (language: {language})"
    if requires_approval:
        tool_call_summary += " (requires approval)"

    print("================================")
    print("Script to be executed")
    print(script)
    print("================================")

    # Create temporary script file
    script_path = "_minicline_tmp_script.py"
    try:
        # Write script to temporary file
        with open(os.path.join(cwd, script_path), "w") as f:
            f.write(script)

        # Execute the script using execute_command
        command = f"python {script_path}"
        _, result = execute_command(
            command=command,
            requires_approval=requires_approval,
            cwd=cwd,
            auto=auto,
            approve_all_commands=approve_all_commands,
            no_container=no_container,
            docker_container=docker_container
        )

    finally:
        # Clean up temporary script file
        try:
            os.remove(os.path.join(cwd, script_path))
        except:
            pass  # Ignore cleanup errors

    return tool_call_summary, result
