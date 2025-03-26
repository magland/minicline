"""Tool for asking follow-up questions to gather additional information."""

from typing import Tuple, List, Optional

def ask_followup_question(question: str, options: Optional[List[str]] = None) -> Tuple[str, str]:
    """Ask a follow-up question to gather additional information.

    Args:
        question: The question to ask
        options: Optional list of predefined answer options

    Returns:
        Tuple of (tool_call_summary, result_text) where:
        - tool_call_summary describes the question asked
        - result_text contains the user's response
    """
    # Format the prompt
    prompt = f"\n{question}"
    if options:
        prompt += "\nOptions:"
        for i, option in enumerate(options, 1):
            prompt += f"\n{i}. {option}"
    prompt += "\nResponse: "

    # Get user input
    response = input(prompt)

    # Build summary
    tool_call_summary = f"Question: {question}"
    if options:
        tool_call_summary += f"\nOptions: {options}"

    return tool_call_summary, response
