"""Tool for writing content to files."""

from pathlib import Path
from typing import Tuple
from .is_within_directory import is_within_directory

def write_to_file(path: str, content: str, *, cwd: str, auto: bool) -> Tuple[str, str]:
    """Write content to a file, creating parent directories if needed.

    Args:
        path: Path to write to (relative to cwd)
        content: Content to write to the file
        cwd: Current working directory
        auto: Whether to automatically approve the action

    Returns:
        Tuple of (tool_call_summary, result_text) where:
        - tool_call_summary is a string describing the tool call
        - result_text indicates success or contains error message
    """
    # For security reasons, check if the file is within the current working directory
    if not is_within_directory(path, cwd):
        raise ValueError(f"ERROR: {path} is not within the current working directory {cwd}")

    tool_call_summary = f"write_to_file for '{path}'"

    print("================================")
    print(f"Content to be written to {path}:")
    print(content)
    print("================================")

    if not auto:
        question = f"Would you like to write this content to {path}? Press ENTER or 'y' to write the content or enter a message to reject this action [y]"
        response = input(f"{question}: ").strip()
        if response.lower() not in ["", "y"]:
            return tool_call_summary, f"User rejected writing content to file with the following message: {response}"

    try:
        # Convert to absolute path if relative
        file_path = Path(cwd) / path

        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write content to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return tool_call_summary, f"Successfully wrote {len(content)} characters to {path}"

    except Exception as e:
        return tool_call_summary, f"ERROR WRITING FILE {path}: {str(e)}"
