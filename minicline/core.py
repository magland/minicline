import re
import sys
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path

from attr import dataclass

from .completion.run_completion import run_completion
from .tools.read_file import read_file
from .tools.read_image import read_image
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
    template_path = Path(__file__).parent / "templates" / "system_prompt.txt"
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

def parse_tool_use_call(content: str) -> Tuple[Optional[str], Union[str, None], Dict[str, Any]]:
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
        return thinking_content, None, {}

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

def execute_tool(tool_name: str, params: Dict[str, Any], cwd: str, auto: bool, approve_all_commands: bool, vision_model: str, no_container: bool) -> Tuple[str, str, Union[str, None], bool, int, int]:
    """Execute a tool and return a tuple of (tool_call_summary, result_text)."""

    try:
        # Tool implementations
        if tool_name == "read_file":
            summary, text = read_file(params['path'], cwd=cwd)
            return summary, text, None, True, 0, 0

        if tool_name == "read_image":
            summary, text, image_data_url, pt, ct = read_image(params['path'], vision_model=vision_model, instructions=params.get('instructions', None), cwd=cwd)
            return summary, text, image_data_url, True, pt, ct

        elif tool_name == "write_to_file":
            summary, text = write_to_file(
                params['path'],
                params['content'],
                cwd=cwd,
                auto=auto
            )
            return summary, text, None, True, 0, 0

        elif tool_name == "replace_in_file":
            summary, text = replace_in_file(
                params['path'],
                params['diff'],
                cwd=cwd,
                auto=auto
            )
            return summary, text, None, True, 0, 0

        elif tool_name == "search_files":
            summary, text = search_files(
                params['path'],
                params['regex'],
                params.get('file_pattern'),
                cwd=cwd
            )
            return summary, text, None, True, 0, 0

        elif tool_name == "execute_command":
            timeout = int(params.get('timeout', 60))  # Default to 60 seconds if not provided
            summary, text = execute_command(
                params['command'],
                params['requires_approval'],
                cwd=cwd,
                auto=auto,
                approve_all_commands=approve_all_commands,
                timeout=timeout,
                no_container=no_container
            )
            return summary, text, None, True, 0, 0

        elif tool_name == "list_files":
            summary, text = list_files(
                params['path'],
                params.get('recursive', False),
                cwd=cwd
            )
            return summary, text, None, True, 0, 0

        elif tool_name == "ask_followup_question":
            if auto:
                # even though the system message doesn't provide this option, it's possible
                # that the AI knows about it anyway. So, let's just reply as appropriate
                return "ask_followup_question", "The user is not able to answer questions because we are in auto mode", None, False, 0, 0
            summary, text = ask_followup_question(
                params['question'],
                params.get('options')
            )
            return summary, text, None, True, 0, 0

        elif tool_name == "attempt_completion":
            summary, text = attempt_completion(
                params['result'],
                auto=auto
            )
            return summary, text, None, True, 0, 0

        else:
            summary = f"Unknown tool '{tool_name}'"
            return summary, "No implementation available", None, False, 0, 0
    except Exception as e:
        # Handle exceptions and return error message
        summary = f"Error executing tool '{tool_name}'"
        text = f"ERROR: {str(e)}"
        return summary, text, None, False, 0, 0

class TeeOutput:
    """Class that duplicates output to both console and log file."""
    def __init__(self, log_file_handle):
        self.stdout = sys.stdout
        self.log_file = log_file_handle

    def write(self, text):
        self.stdout.write(text)
        if self.log_file:
            self.log_file.write(text)
            self.log_file.flush()

    def flush(self):
        self.stdout.flush()
        if self.log_file:
            self.log_file.flush()

@dataclass
class PerformTaskResult:
    total_prompt_tokens: int
    total_completion_tokens: int
    total_vision_prompt_tokens: int
    total_vision_completion_tokens: int

def perform_task(instructions: str, *, cwd: str | None = None, model: str | None = None, vision_model: str | None=None, log_file: str | Path | None = None, auto: bool = False, approve_all_commands: bool = False, no_container: bool = False) -> PerformTaskResult:
    """Perform a task based on the given instructions.

    Args:
        instructions: The task instructions
        cwd: Optional working directory for the task
        model: Optional model to use for completion
        vision_model: Optional model to use for vision tasks
        log_file: Optional file path to write verbose logs to
        auto: Whether to run in automatic mode where no user input is required and all actions proposed by the AI are taken (except when commands require approval and approve_all_commands is False)
        approve_all_commands: Whether to automatically approve all commands that require approval
        no_container: Whether to run commands without a container (default: False)

    Returns:
        Tuple of (total_prompt_tokens
        total_completion_tokens)
    """
    if not cwd:
        cwd = os.getcwd()

    if not model:
        model = "google/gemini-2.0-flash-001"

    if not vision_model:
        vision_model = model

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
    total_vision_prompt_tokens = 0
    total_vision_completion_tokens = 0

    # Open log file if specified and set up output redirection
    log_file_handle = open(log_file, 'w') if log_file else None
    original_stdout = sys.stdout

    print("TASK INSTRUCTIONS:")
    print(instructions)
    print("")

    num_consecutive_failures = 0
    try:
        if log_file_handle:
            sys.stdout = TeeOutput(log_file_handle)
        # Main conversation loop
        while True:
            # Get assistant's response
            content, messages, prompt_tokens, completion_tokens = run_completion_with_retries(
                messages=messages,
                model=model,
                num_retries=5
            ) # type: ignore
            total_prompt_tokens += prompt_tokens
            total_completion_tokens += completion_tokens

            # Parse and execute tool if found
            thinking_content, tool_name, params = parse_tool_use_call(content) # type: ignore
            if not tool_name:
                print('content: ', content)
                print("No tool use found. Please provide a tool use in the following format: <thinking>...</thinking><tool_name><param1>value1</param1><param2>value2</param2></tool_name>")
                num_consecutive_failures += 1
                if num_consecutive_failures > 3:
                    raise Exception("Too many consecutive failures. Exiting.")
                messages.append({"role": "system", "content": "No tool use found. Please provide a tool use in the following format: <thinking>...</thinking><tool_name><param1>value1</param1><param2>value2</param2></tool_name>"})
                continue

            if thinking_content:
                print(thinking_content)

            print(f"\nTool: {tool_name}")
            print(f"Params: {params}")

            tool_call_summary, tool_result_text, image_data_url, handled, additional_vision_prompt_tokens, additional_vision_completion_tokens = execute_tool(tool_name, params, cwd, auto=auto, approve_all_commands=approve_all_commands, vision_model=vision_model, no_container=no_container)
            total_vision_prompt_tokens += additional_vision_prompt_tokens
            total_vision_completion_tokens += additional_vision_completion_tokens
            if not handled:
                num_consecutive_failures += 1
                if num_consecutive_failures > 3:
                    raise Exception("Too many consecutive failures. Exiting.")
            else:
                num_consecutive_failures = 0

            print(f"Total prompt tokens: {total_prompt_tokens} + {total_vision_prompt_tokens}")
            print(f"Total completion tokens: {total_completion_tokens} + {total_vision_completion_tokens}")
            print("")

            if tool_result_text == "TASK_COMPLETE":
                if log_file_handle:
                    log_file_handle.close()
                break

            # Print the result of the tool
            print("=========================================")
            print(f"\n{tool_call_summary}:")
            print(tool_result_text)
            print("=========================================")
            print("")

            base_env = get_base_env(cwd=cwd)
            content: List[Dict[str, Any]] = [
                {'type': 'text', 'text': f"[{tool_call_summary}] Result:"},
                {'type': 'text', 'text': tool_result_text},
            ]
            if image_data_url:
                content.append({'type': 'image_url', 'image_url': {'url': image_data_url}})
            content.append(
                {'type': 'text', 'text': base_env}
            )
            messages.append({
                "role": "user",
                "content": content
            })
    finally:
        # Restore original stdout and close log file
        if log_file_handle:
            sys.stdout = original_stdout
            log_file_handle.close()

    return PerformTaskResult(
        total_prompt_tokens=total_prompt_tokens,
        total_completion_tokens=total_completion_tokens,
        total_vision_prompt_tokens=total_vision_prompt_tokens,
        total_vision_completion_tokens=total_vision_completion_tokens
    )

def get_base_env(*, cwd: str) -> str:
    # Get list of files using breadth-first search, limited to certain number of files
    max_num_files = 25
    files = []
    dirs_to_process = [Path(cwd)]
    processed_dirs = set()

    while dirs_to_process and len(files) < max_num_files:
        current_dir = dirs_to_process.pop(0)

        # never process node_modules
        if 'node_modules' in str(current_dir):
            continue

        # never process .git
        if '.git' in str(current_dir):
            continue

        # never process .venv
        if '.venv' in str(current_dir):
            continue

        # never process __pycache__
        if '__pycache__' in str(current_dir):
            continue

        if current_dir in processed_dirs:
            continue

        processed_dirs.add(current_dir)

        try:
            # First add files in current directory
            for path in current_dir.iterdir():
                if len(files) >= max_num_files:
                    break

                if path.is_file():
                    # Get relative path from cwd
                    rel_path = str(path.relative_to(cwd))
                    files.append(rel_path)
                elif path.is_dir():
                    dirs_to_process.append(path)
        except PermissionError:
            continue  # Skip directories we can't access

    # Sort files for consistent output
    files.sort()
    files_str = '\n'.join(files)

    base_env = f"<environment_details>\nCurrent Working Directory: {cwd}\n\n# Working Directory Files (Recursive)\n{files_str}\n</environment_details>"
    return base_env


def run_completion_with_retries(
        messages: List[Dict[str, Any]], *,
        model: str,
        num_retries: int
    ) -> Tuple[str, List[Dict[str, Any]], int, int]:
    """Run completion with retries in case of failure."""
    import time
    retry_wait_time = 1
    for i in range(num_retries):
        try:
            return run_completion(messages, model=model)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error running completion: {e}")
            print(f"Retrying in {retry_wait_time} seconds...")
            time.sleep(retry_wait_time)
            retry_wait_time *= 2
    raise Exception(f"Failed to run completion after {num_retries} retries")
