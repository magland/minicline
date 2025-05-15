import click
from pathlib import Path
from .core import perform_task

@click.group()
def cli():
    """Command-line interface for executing tasks using large language models"""
    pass

@cli.command("perform-task")
@click.argument('instructions', required=False)
@click.option('--file', '-f', type=click.Path(exists=True, path_type=Path), help='File containing task instructions')
@click.option('--model', '-m', help='Model to use for completion (default: google/gemini-2.0-flash-001)')
@click.option('--vision-model', default=None, help='Model to use for vision tasks (default: same as --model)')
@click.option('--log-file', '-l', type=click.Path(dir_okay=False, path_type=Path), help='File to write verbose logs to')
@click.option('--auto', is_flag=True, help='Run in automatic mode where no user input is required and all actions proposed by the AI are taken (except for commands that require approval when approve_all_commands is not set)')
@click.option('--approve-all-commands', is_flag=True, help='Automatically approve all commands that require approval')
@click.option('--no-container', is_flag=True, help='Do not run commands in a container. Dangerous, especially if used with --auto and/or --approve-all-commands')
def perform_task_cmd(instructions: str | None, file: Path | None, model: str | None, vision_model: str | None, log_file: Path | None, auto: bool, approve_all_commands: bool, no_container: bool):
    """Execute a task using provided instructions or from a file.

    You can provide instructions directly as an argument:
        minicline perform-task "create a hello world script"

    Or use a file containing the instructions:
        minicline perform-task -f instructions.txt

    Recommended OpenRouter Models:
        - google/gemini-2.0-flash-001
        - anthropic/claude-3.5-sonnet
        - anthropic/claude-3.7-sonnet
    """
    if file:
        instructions = file.read_text()
    elif not instructions:
        raise click.UsageError("Either instructions argument or --file option is required")

    perform_task(instructions, model=model, vision_model=vision_model, log_file=log_file, auto=auto, approve_all_commands=approve_all_commands, no_container=no_container)

if __name__ == "__main__":
    cli()
