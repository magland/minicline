"""Tool for searching files with regex patterns."""

import re
from pathlib import Path
from typing import Tuple, Optional
from .is_within_directory import is_within_directory

def search_files(path: str, regex: str, file_pattern: Optional[str] = None, *, cwd: str) -> Tuple[str, str]:
    """Search files in a directory for a regex pattern.

    Args:
        path: Directory path to search in (relative to cwd)
        regex: Regular expression pattern to search for
        file_pattern: Optional glob pattern to filter files
        cwd: Current working directory

    Returns:
        Tuple of (tool_call_summary, result_text) where:
        - tool_call_summary is a string describing the tool call
        - result_text contains the search results with context
    """
    # For security reasons, check if the file is within the current working directory
    if not is_within_directory(path, cwd):
        raise ValueError(f"ERROR: {path} is not within the current working directory {cwd}")

    tool_call_summary = f"search_files in '{path}' for pattern '{regex}'"
    if file_pattern:
        tool_call_summary += f" (files matching '{file_pattern}')"

    try:
        # Convert to absolute path if relative
        search_path = Path(cwd) / path
        if not search_path.exists():
            return tool_call_summary, f"ERROR: Directory '{path}' does not exist"

        try:
            pattern = re.compile(regex)
        except re.error as e:
            return tool_call_summary, f"ERROR: Invalid regex pattern: {str(e)}"

        results = []
        # Recursively search through files
        for file_path in search_path.rglob('*'):
            if not file_path.is_file():
                continue

            # Apply file pattern filter if provided
            if file_pattern:
                if not file_path.match(file_pattern):
                    continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                # Search through lines with context
                for i, line in enumerate(lines):
                    if pattern.search(line):
                        # Get context (3 lines before and after)
                        start = max(0, i - 3)
                        end = min(len(lines), i + 4)
                        context = ''.join(lines[start:end])

                        # Add file path and match details
                        rel_path = file_path.relative_to(search_path)
                        results.append(f"\nFile: {rel_path} (line {i + 1})\n{'-' * 40}\n{context}\n")

            except UnicodeDecodeError:
                # Skip binary files
                continue
            except Exception as e:
                results.append(f"\nERROR reading {file_path}: {str(e)}\n")

        if not results:
            return tool_call_summary, "No matches found"

        return tool_call_summary, ''.join(results)

    except Exception as e:
        return tool_call_summary, f"ERROR: {str(e)}"
