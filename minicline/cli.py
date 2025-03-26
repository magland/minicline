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
def perform_task_cmd(instructions: str | None, file: Path | None):
    """Execute a task using provided instructions or from a file.

    You can provide instructions directly as an argument:
        minicline perform-task "create a hello world script"

    Or use a file containing the instructions:
        minicline perform-task -f instructions.txt
    """
    if file:
        instructions = file.read_text()
    elif not instructions:
        raise click.UsageError("Either instructions argument or --file option is required")

    perform_task(instructions)

if __name__ == "__main__":
    cli()
