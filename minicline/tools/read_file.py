"""Tool for reading file contents."""

from pathlib import Path
from typing import Tuple

def read_file(path: str, *, cwd: str) -> Tuple[str, str]:
    """Read the contents of a file.

    Args:
        path: Path to the file to read (relative to cwd)
        cwd: Current working directory

    Returns:
        Tuple of (tool_call_summary, result_text) where:
        - tool_call_summary is a string describing the tool call
        - result_text is either the file contents or an error message
    """
    tool_call_summary = f"read_file for '{path}'"

    try:
        # Convert to absolute path if relative
        file_path = Path(cwd) / path

        # Read and return contents
        with open(file_path, 'r', encoding='utf-8') as f:
            return tool_call_summary, f.read()

    except Exception as e:
        return tool_call_summary, f"ERROR READING FILE {path}: {str(e)}"
