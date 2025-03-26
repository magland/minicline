"""Tool for writing content to files."""

from pathlib import Path
from typing import Tuple

def write_to_file(path: str, content: str, *, cwd: str) -> Tuple[str, str]:
    """Write content to a file, creating parent directories if needed.

    Args:
        path: Path to write to (relative to cwd)
        content: Content to write to the file
        cwd: Current working directory

    Returns:
        Tuple of (tool_call_summary, result_text) where:
        - tool_call_summary is a string describing the tool call
        - result_text indicates success or contains error message
    """
    tool_call_summary = f"write_to_file for '{path}'"

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
