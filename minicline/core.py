import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from .completion.run_completion import run_completion
from .tools.read_file import read_file
from .tools.search_files import search_files
from .tools.execute_command import execute_command
from .tools.list_files import list_files
from .tools.ask_followup_question import ask_followup_question
from .tools.write_to_file import write_to_file
from .tools.replace_in_file import replace_in_file
from .tools.attempt_completion import attempt_completion
import os

def read_system_prompt(*, cwd: str | None, auto: bool = False) -> str:
    """Read and process the system prompt template."""
    template_path = Path(__file__).parent / "templates" / "system_prompt.md"
    with open(template_path, "r") as f:
        content = f.read()

    if cwd:
        content = content.replace("{{ cwd }}", cwd)

    # In auto mode, remove sections and their markers
    if auto:
        content = re.sub(
            r'=== begin if not auto ===\n.*?=== end if not auto ===\n',
            '',
            content,
            flags=re.DOTALL
        )
    else:
        # Otherwise just remove the markers
        content = re.sub(
            r'=== (begin|end) if not auto ===\n',
            '',
            content
        )

    return content

def parse_tool_use_call(content: str) -> Optional[Tuple[Optional[str], str, Dict[str, Any]]]:
    """Parse a tool use from the assistant's message.

    Args:
        content: The content to parse

    Returns:
        Tuple of (thinking_content, tool_name, params_dict) if found, None if no tool use found
        thinking_content may be None if no thinking tags present
    """
    # First try to extract thinking content
    thinking_pattern = r"<thinking>(.*?)</thinking>"
    thinking_match = re.search(thinking_pattern, content, re.DOTALL)
    thinking_content = thinking_match.group(1).strip() if thinking_match else None

    # Basic XML parsing for tool use - could be improved with proper XML parser
    pattern = r"<(\w+)>(.*?)</\1>"
    remaining_content = content[thinking_match.end():] if thinking_match else content
    tool_match = re.search(pattern, remaining_content, re.DOTALL)
    if not tool_match:
        return None

    tool_name = tool_match.group(1)
    tool_content = tool_match.group(2)

    # Parse parameters
    params = {}
    param_matches = re.finditer(r"<(\w+)>(.*?)</\1>", tool_content, re.DOTALL)
    for match in param_matches:
        param_name = match.group(1)
        param_value = match.group(2).strip()
        if param_name == "options": # Handle array parameter
            try:
                param_value = eval(param_value)  # Convert string array to actual array
            except:
                param_value = []
        params[param_name] = param_value
    return thinking_content, tool_name, params

def execute_tool(tool_name: str, params: Dict[str, Any], cwd: str, auto: bool, approve_all_commands: bool) -> Tuple[str, str]:
    """Execute a tool and return a tuple of (tool_call_summary, result_text)."""

    # Tool implementations
    if tool_name == "read_file":
        return read_file(params['path'], cwd=cwd)

    elif tool_name == "write_to_file":
        return write_to_file(
            params['path'],
            params['content'],
            cwd=cwd,
            auto=auto
        )

    elif tool_name == "replace_in_file":
        return replace_in_file(
            params['path'],
            params['diff'],
            cwd=cwd,
            auto=auto
        )

    elif tool_name == "search_files":
        return search_files(
            params['path'],
            params['regex'],
            params.get('file_pattern'),
            cwd=cwd
        )

    elif tool_name == "execute_command":
        return execute_command(
            params['command'],
            params['requires_approval'],
            cwd=cwd,
            auto=auto,
            approve_all_commands=approve_all_commands
        )

    elif tool_name == "list_files":
        return list_files(
            params['path'],
            params.get('recursive', False),
            cwd=cwd
        )

    elif tool_name == "ask_followup_question":
        if auto:
            # even though the system message doesn't provide this option, it's possible
            # that the AI knows about it anyway. So, let's just reply as appropriate
            return "ask_followup_question", "The user is not able to answer questions because we are in auto mode"
        return ask_followup_question(
            params['question'],
            params.get('options')
        )

    elif tool_name == "attempt_completion":
        return attempt_completion(
            params['result'],
            auto=auto
        )

    else:
        summary = f"Unknown tool '{tool_name}'"
        return summary, "No implementation available"

def perform_task(instructions: str, *, cwd: str | None = None, model: str | None = None, log_file: str | Path | None = None, auto: bool = False, approve_all_commands: bool = False) -> None:
    """Perform a task based on the given instructions.

    Args:
        instructions: The task instructions
        cwd: Optional working directory for the task
        model: Optional model to use for completion
        log_file: Optional file path to write verbose logs to
        auto: Whether to run in automatic mode where no user input is required and all actions proposed by the AI are taken (except when commands require approval and approve_all_commands is False)
        approve_all_commands: Whether to automatically approve all commands that require approval
    """
    if not cwd:
        cwd = os.getcwd()

    if not model:
        model = "google/gemini-2.0-flash-001"

    # Initialize conversation with system prompt
    system_prompt = read_system_prompt(cwd=cwd, auto=auto)
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": system_prompt}
    ]

    # Add initial user message with task instructions
    base_env = get_base_env(cwd=cwd)
    user_message = f"<task>\n{instructions}\n</task>\n\n{base_env}"
    messages.append({"role": "user", "content": [
        {'type': 'text', 'text': user_message},
        {'type': 'text', 'text': base_env}
    ]})

    total_prompt_tokens = 0
    total_completion_tokens = 0

    # Open log file if specified
    log_file_handle = open(log_file, 'w') if log_file else None

    try:
        # Main conversation loop
        while True:
            # Get assistant's response
            content, messages, prompt_tokens, completion_tokens = run_completion(messages, model=model)
            total_prompt_tokens += prompt_tokens
            total_completion_tokens += completion_tokens

            # Parse and execute tool if found
            tool_use_call = parse_tool_use_call(content)
            if not tool_use_call:
                error_msg = "\nNo valid tool use found in assistant's message\nMessage content: " + content
                print(error_msg)
                if log_file_handle:
                    log_file_handle.write(error_msg + "\n")
                raise Exception("Assistant did not use a valid tool")

            thinking_content, tool_name, params = tool_use_call

            if thinking_content:
                msg = f"\nThinking: {thinking_content}"
                print(msg)
                if log_file_handle:
                    log_file_handle.write(msg + "\n")

            # Print and log the tool name and number of tokens
            def log(msg: str):
                print(msg)
                if log_file_handle:
                    log_file_handle.write(msg + '\n')
                    log_file_handle.flush()

            log(f"\nTool: {tool_name}")
            log(f"Params: {params}")
            log(f"Total prompt tokens: {total_prompt_tokens}")
            log(f"Total completion tokens: {total_completion_tokens}")
            log("")

            tool_call_summary, tool_result_text = execute_tool(tool_name, params, cwd, auto=auto, approve_all_commands=approve_all_commands)

            if tool_result_text == "TASK_COMPLETE":
                if log_file_handle:
                    log_file_handle.close()
                break

            # Print and log the result of the tool
            log("=========================================")
            log(f"\n{tool_call_summary}:")
            log(tool_result_text)
            log("=========================================")
            log("")

            # Add tool result as next user message
            base_env = get_base_env(cwd=cwd)
            messages.append({
                "role": "user",
                "content": [
                    {'type': 'text', 'text': f"[{tool_call_summary}] Result:"},
                    {'type': 'text', 'text': tool_result_text},
                    {'type': 'text', 'text': base_env}
                ]
            })
    finally:
        # Ensure log file is closed even if an error occurs
        if log_file_handle:
            log_file_handle.close()

def get_base_env(*, cwd: str) -> str:
    # Get recursive list of files using Path
    files = []
    for path in Path(cwd).rglob('*'):
        if path.is_file():
            # Get relative path from cwd
            rel_path = str(path.relative_to(cwd))
            files.append(rel_path)

    # Sort files for consistent output
    files.sort()
    files_str = '\n'.join(files)

    base_env = f"<environment_details>\nCurrent Working Directory: {cwd}\n\n# Working Directory Files (Recursive)\n{files_str}\n</environment_details>"
    return base_env
