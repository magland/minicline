"""Tool for replacing content in files using search/replace blocks."""

from pathlib import Path
from typing import Tuple
import re
from .is_within_directory import is_within_directory

def parse_search_replace_blocks(diff: str) -> list[tuple[str, str]]:
    """Extract search/replace blocks from diff content.

    Args:
        diff: String containing one or more search/replace blocks

    Returns:
        List of tuples (search_content, replace_content)
    """
    pattern = r'<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE'
    blocks = []

    for match in re.finditer(pattern, diff, re.DOTALL):
        search_content = match.group(1)
        replace_content = match.group(2)
        blocks.append((search_content, replace_content))

    return blocks

def replace_in_file(path: str, diff: str, *, cwd: str, auto: bool) -> Tuple[str, str]:
    """Replace content in a file using search/replace blocks.

    Args:
        path: Path to the file to modify (relative to cwd)
        diff: String containing one or more search/replace blocks
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

    tool_call_summary = f"replace_in_file for '{path}'"

    print("================================")
    print(f"Proposed replacement in {path}:")
    print(diff)
    print("================================")

    if not auto:
        question = f"Would you like to make this change to {path}? Press ENTER or 'y' to write the change or enter a message to reject this action [y]"
        response = input(f"{question}: ").strip()
        if response.lower() not in ["", "y"]:
            return tool_call_summary, f"User rejected replacing content to file with the following message: {response}"

    try:
        # Convert to absolute path if relative
        file_path = Path(cwd) / path

        # Read current file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse and apply search/replace blocks
        blocks = parse_search_replace_blocks(diff)
        if not blocks:
            return tool_call_summary, "ERROR: No valid search/replace blocks found in diff"

        modified_content = content
        replacements_made = 0

        for search_content, replace_content in blocks:
            if search_content not in modified_content:
                return tool_call_summary, f"ERROR: Search content not found:\n{search_content}"

            # Only replace first occurrence as per requirements
            modified_content = modified_content.replace(search_content, replace_content, 1)
            replacements_made += 1

        # Write modified content back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)

        return tool_call_summary, f"Successfully made {replacements_made} replacements in {path}"

    except Exception as e:
        return tool_call_summary, f"ERROR MODIFYING FILE {path}: {str(e)}"
