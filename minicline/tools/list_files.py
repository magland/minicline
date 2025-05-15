"""Tool for listing directory contents."""

from pathlib import Path
from typing import Tuple
from .is_within_directory import is_within_directory

def list_files(path: str, recursive: bool = False, *, cwd: str) -> Tuple[str, str]:
    """List contents of a directory.

    Args:
        path: Path to the directory to list (relative to cwd)
        recursive: Whether to list recursively
        cwd: Current working directory

    Returns:
        Tuple of (tool_call_summary, result_text) where:
        - tool_call_summary is a string describing the tool call
        - result_text is the directory listing or error message
    """
    # For security reasons, check if the file is within the current working directory
    if not is_within_directory(path, cwd):
        raise ValueError(f"ERROR: {path} is not within the current working directory {cwd}")

    tool_call_summary = f"list_files for '{path}'"
    if recursive:
        tool_call_summary += " (recursive)"

    try:
        # Convert to absolute path if relative
        dir_path = Path(cwd) / path

        # Verify directory exists
        if not dir_path.exists():
            return tool_call_summary, f"ERROR: Directory not found: {path}"
        if not dir_path.is_dir():
            return tool_call_summary, f"ERROR: Not a directory: {path}"

        # Get file listing
        if recursive:
            entries = list(dir_path.rglob('*'))
        else:
            entries = list(dir_path.iterdir())

        # Format output
        output_lines = []
        for entry in sorted(entries):
            # Get path relative to the requested directory
            rel_path = entry.relative_to(dir_path)
            type_indicator = '/' if entry.is_dir() else ''
            output_lines.append(f"{rel_path}{type_indicator}")

        if not output_lines:
            return tool_call_summary, "Directory is empty"

        return tool_call_summary, "\n".join(output_lines)

    except Exception as e:
        return tool_call_summary, f"ERROR listing directory: {str(e)}"
