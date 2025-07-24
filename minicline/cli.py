import click
from pathlib import Path
from .core import perform_task
from .docker_manager import DockerManager

@click.group()
def cli():
    """Command-line interface for executing tasks using large language models"""
    pass

@cli.group("docker")
def docker_group():
    """Docker container management commands"""
    pass

@docker_group.command("start")
@click.argument('image', default='jupyter/scipy-notebook:latest')
@click.option('--name', '-n', help='Container name (optional, will generate if not provided)')
def docker_start(image: str, name: str | None):
    """Start a persistent Docker container for minicline tasks.

    IMAGE: Docker image to use (default: jupyter/scipy-notebook:latest)

    Returns the container name which can be used with --docker option.
    """
    import os
    cwd = os.getcwd()
    manager = DockerManager(cwd)

    try:
        container_name = manager.start_container(image, name)
        print(f"\nContainer started successfully!")
        print(f"Container name: {container_name}")
        print(f"\nTo use this container with minicline, run:")
        print(f"minicline perform-task --docker {container_name} \"your task here\"")
    except Exception as e:
        print(f"Error starting container: {e}")
        raise click.ClickException(str(e))

@docker_group.command("stop")
@click.argument('container_name')
def docker_stop(container_name: str):
    """Stop and remove a persistent Docker container.

    CONTAINER_NAME: Name of the container to stop
    """
    import os
    cwd = os.getcwd()
    manager = DockerManager(cwd)

    try:
        success = manager.stop_container(container_name)
        if success:
            print(f"Container {container_name} stopped and removed successfully")
        else:
            raise click.ClickException(f"Failed to stop container {container_name}")
    except Exception as e:
        print(f"Error stopping container: {e}")
        raise click.ClickException(str(e))

@docker_group.command("list")
def docker_list():
    """List all minicline Docker containers"""
    import os
    cwd = os.getcwd()
    manager = DockerManager(cwd)

    try:
        containers = manager.list_containers()
        if not containers:
            print("No minicline containers found")
            return

        print("Minicline Docker containers:")
        print("-" * 80)
        print(f"{'NAME':<30} {'STATUS':<15} {'IMAGE':<25} {'CREATED'}")
        print("-" * 80)
        for name, info in containers.items():
            print(f"{name:<30} {info['status']:<15} {info['image']:<25} {info['created']}")
    except Exception as e:
        print(f"Error listing containers: {e}")
        raise click.ClickException(str(e))

@cli.command("perform-task")
@click.argument('instructions', required=False)
@click.option('--file', '-f', type=click.Path(exists=True, path_type=Path), help='File containing task instructions')
@click.option('--model', '-m', help='Model to use for completion (default: openai/gpt-4.1-mini)')
@click.option('--vision-model', default=None, help='Model to use for vision tasks (default: same as --model)')
@click.option('--log-file', '-l', type=click.Path(dir_okay=False, path_type=Path), help='File to write verbose logs to')
@click.option('--auto', is_flag=True, help='Run in automatic mode where no user input is required and all actions proposed by the AI are taken (except for commands that require approval when approve_all_commands is not set)')
@click.option('--approve-all-commands', is_flag=True, help='Automatically approve all commands that require approval')
@click.option('--no-container', is_flag=True, help='Do not run commands in a container. Dangerous, especially if used with --auto and/or --approve-all-commands')
@click.option('--docker', help='Use existing Docker container for command execution (container name)')
@click.option('--rules', type=click.Path(exists=True, path_type=Path), default=None, help='File containing additional rules to include')
def perform_task_cmd(instructions: str | None, file: Path | None, model: str | None, vision_model: str | None, log_file: Path | None, auto: bool, approve_all_commands: bool, no_container: bool, docker: str | None, rules: Path | None):
    """Execute a task using provided instructions or from a file.

    You can provide instructions directly as an argument:
        minicline perform-task "create a hello world script"

    Or use a file containing the instructions:
        minicline perform-task -f instructions.txt

    Recommended OpenRouter Models:
        - openai/gpt-4.1-mini
        - anthropic/claude-3.5-sonnet
        - anthropic/claude-3.7-sonnet
    """
    if file:
        instructions = file.read_text()
    elif not instructions:
        raise click.UsageError("Either instructions argument or --file option is required")

    perform_task(instructions, model=model, vision_model=vision_model, log_file=log_file, auto=auto, approve_all_commands=approve_all_commands, no_container=no_container, docker_container=docker, rules=rules)

if __name__ == "__main__":
    cli()
