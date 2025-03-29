"""Tool for reading file contents."""

from pathlib import Path
from typing import Tuple, Union
import base64

def read_image(path: str, *, cwd: str) -> Tuple[str, str, Union[str, None]]:
    """Read the contents of a file.

    Args:
        path: Path to the PNG file to read (relative to cwd)
        cwd: Current working directory

    Returns:
        Tuple of (tool_call_summary, data_url) where:
        - tool_call_summary is a string describing the tool call
        - data_url is a base64-encoded PNG image data URL
    """
    tool_call_summary = f"read_image for '{path}'"

    try:
        rel_file_path = Path(path)
        # Convert to absolute path if relative
        file_path = Path(cwd) / path

        # Read and return contents
        with open(file_path, 'rb') as f:
            data = f.read()
            data_base64 = base64.b64encode(data).decode('utf-8')
            data_url = f"data:image/png;base64,{data_base64}"
            return tool_call_summary, f'The image for {rel_file_path} is attached.', data_url

    except Exception as e:
        return tool_call_summary, f"ERROR READING FILE {path}: {str(e)}", None
