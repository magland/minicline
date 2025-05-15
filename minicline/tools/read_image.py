"""Tool for reading file contents."""

from pathlib import Path
from typing import Tuple, Union, List, Dict, Any
import base64
from ..completion.run_completion import run_completion
from .is_within_directory import is_within_directory

def read_image(path: str, *, instructions: Union[str, None], cwd: str, vision_model: Union[str, None]) -> Tuple[str, str, Union[str, None], int, int]:
    """Read the contents of a file.

    Args:
        path: Path to the PNG file to read (relative to cwd)
        cwd: Current working directory
        vision_model: AI model to use for image analysis
        instructions: Instructions for the AI model for image analysis

    Returns:
        Tuple of (tool_call_summary, data_url) where:
        - tool_call_summary is a string describing the tool call
        - data_url is a base64-encoded PNG image data URL
    """
    # For security reasons, check if the file is within the current working directory
    if not is_within_directory(path, cwd):
        raise ValueError(f"ERROR: {path} is not within the current working directory {cwd}")

    tool_call_summary = f"read_image for '{path}'"

    prompt_tokens = 0
    completion_tokens = 0
    try:
        rel_file_path = Path(path)
        # Convert to absolute path if relative
        file_path = Path(cwd) / path

        # Read and return contents
        with open(file_path, 'rb') as f:
            data = f.read()
            data_base64 = base64.b64encode(data).decode('utf-8')
            data_url = f"data:image/png;base64,{data_base64}"
            if vision_model:
                ai_description, prompt_tokens, completion_tokens = _get_ai_description(data_url, vision_model=vision_model, instructions=instructions)
            else:
                ai_description = None
            text = f'The image for {rel_file_path} is attached.'
            if ai_description:
                text += f' AI description: {ai_description}'
            return tool_call_summary, text, data_url, prompt_tokens, completion_tokens

    except Exception as e:
        return tool_call_summary, f"ERROR READING FILE {path}: {str(e)}", None, prompt_tokens, completion_tokens


def _get_ai_description(data_url: str, *, vision_model: str, instructions: Union[str, None]) -> Tuple[str, int, int]:
    """Get AI description for the image.

    Args:
        data_url: Base64-encoded PNG image data URL
        vision_model: AI model to use
        instructions: Instructions for the AI model

    Returns:
        AI description for the image
    """
    txt = 'Analyze the attached image and provide a concise description.'
    if instructions:
        txt += f' The provided instructions are: {instructions}. Please be concise.'
    content: List[Dict[str, Any]] = [
        {'type': 'text', 'text': txt},
        {'type': 'image_url', 'image_url': {'url': data_url}}
    ]
    messages: List[Dict[str, Any]] = [
        {
            "role": "system",
            "content": "You are an expert at analyzing images."
        },
        {
            "role": "user",
            "content": content
        }
    ]
    content, _, prompt_tokens, completion_tokens = run_completion(messages, model=vision_model)  # type: ignore
    return content, prompt_tokens, completion_tokens  # type: ignore
