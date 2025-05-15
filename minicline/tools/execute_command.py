"""Tool for executing system commands."""

import os
import select
import signal
import subprocess
import time
from typing import Tuple

def execute_command(command: str, requires_approval: bool, *, cwd: str, auto: bool, approve_all_commands: bool, timeout: int = 60, no_container: bool) -> Tuple[str, str]:
    """Execute a system command.

    Args:
        command: The command to execute
        requires_approval: Whether the command requires explicit user approval
        cwd: Current working directory
        auto: Whether running in automatic mode
        approve_all_commands: Whether to automatically approve all commands
        timeout: Maximum time in seconds to wait for command completion (default: 60, 0 for no timeout)

    Returns:
        Tuple of (tool_call_summary, result_text) where:
        - tool_call_summary is a string describing the tool call
        - result_text contains the command output or error message
    """
    if not no_container:
        default_docker_image = "jupyter/scipy-notebook:latest"
        docker_image = os.getenv("MINICLINE_DOCKER_IMAGE", default_docker_image)
    else:
        docker_image = None
    use_apptainer = os.getenv("MINICLINE_USE_APPTAINER", "false").lower() == "true"

    tool_call_summary = f"execute_command '{command}'"
    if requires_approval:
        tool_call_summary += " (requires approval)"

    print("================================")
    print("Command to be executed")
    print(command)
    if docker_image:
        if use_apptainer:
            print(f"Using apptainer exec with docker image: {docker_image}")
        else:
            print(f"Using docker image: {docker_image}")
    print("================================")

    ask_user = True
    if approve_all_commands:
        ask_user = False
    if auto and not requires_approval:
        ask_user = False

    if ask_user:
        if requires_approval:
            question = f"Would you like to execute the above command (requires approval)? Press ENTER or 'y' to execute the command or enter a message to reject this action [y]"
        else:
            question = f"Would you like to execute the above command? Press ENTER or 'y' to execute the command or enter a message to reject this action [y]"
        response = input(f"{question}: ").strip()
        if response.lower() not in ["", "y"]:
            return tool_call_summary, f"User rejected executing the command with the following message: {response}"

    try:
        # Run command and capture output
        process = None
        stdout = ""
        stderr = ""
        use_docker = docker_image is not None
        container_name = None
        try:
            if use_docker:
                if use_apptainer:
                    # Construct the apptainer command
                    apptainer_cmd = [
                        "apptainer", "exec",
                        "--bind", f"{cwd}:{cwd}",  # Mount current directory
                        "--pwd", cwd,  # Set working directory
                        f"docker://{docker_image}",
                        "/bin/sh", "-c", command
                    ]
                    shell = False
                    full_command = apptainer_cmd
                    container_name = None
                else:
                    # Pull the docker image first
                    print(f"Pulling docker image: {docker_image}")
                    subprocess.run(["docker", "pull", docker_image], check=True)

                    # Generate a unique container name
                    container_name = f"minicline_sandbox_{int(time.time())}"
                    # Construct the docker command
                    docker_cmd = [
                        "docker", "run",
                        "--rm",  # Auto-remove container when it exits
                        "--name", container_name,
                        "-v", f"{cwd}:{cwd}",  # Mount current directory
                        "-w", cwd,  # Set working directory
                        "-t",  # Allocate a pseudo-TTY
                        docker_image,
                        "/bin/sh", "-c", command
                    ]
                    shell = False
                    full_command = docker_cmd
            else:
                # If not using docker, run the command directly
                shell = True
                full_command = command

            # Start process in its own process group so we can kill it and its children
            process = subprocess.Popen(
                full_command,
                shell=shell,
                cwd=cwd,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )

            # Use select to handle output while checking for timeout
            start_time = time.time()
            reads = []
            if process and process.stdout:
                reads.append(process.stdout.fileno())
            if process and process.stderr:
                reads.append(process.stderr.fileno())

            while True:
                # Check if process has finished
                if process.poll() is not None:
                    break

                # Check for timeout
                if timeout > 0 and time.time() - start_time > timeout:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)  # Kill process group
                    time.sleep(0.1)  # Give process time to terminate
                    if process.poll() is None:  # If still running
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)  # Force kill
                    # Format timeout output including captured stdout/stderr
                    output_parts = [f"Command timed out after {timeout} seconds and was forcefully terminated"]
                    if stdout:
                        output_parts.append(f"STDOUT (partial):\n{stdout}")
                    if stderr:
                        output_parts.append(f"STDERR (partial):\n{stderr}")
                    return tool_call_summary, "\n".join(output_parts)

                # Read available output
                if reads:  # Only try to read if we have file descriptors
                    readable, _, _ = select.select(reads, [], [], 0.1)  # 0.1s timeout
                    for fd in readable:
                        if process.stdout and fd == process.stdout.fileno():
                            chunk = os.read(fd, 4096)  # Read raw bytes
                            if chunk:
                                output = chunk.decode()
                                stdout += output
                                print(output, end="", flush=True)
                        if process.stderr and fd == process.stderr.fileno():
                            chunk = os.read(fd, 4096)  # Read raw bytes
                            if chunk:
                                output = chunk.decode()
                                stderr += output
                                print(output, end="", flush=True)

            # Get final output and return code
            final_stdout, final_stderr = process.communicate()
            stdout += final_stdout
            stderr += final_stderr
            returncode = process.returncode

        except Exception as e:
            if process and process.poll() is None:
                try:
                    # If using docker and we have a container name, stop it first
                    if use_docker and not use_apptainer and container_name is not None:
                        subprocess.run(["docker", "stop", str(container_name)], check=False, capture_output=True)
                    time.sleep(0.1)
                    # Then kill the process group
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    time.sleep(0.1)
                    if process.poll() is None:
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                except:
                    pass
            raise e

        # Format output including both stdout and stderr
        output_parts = []
        if stdout:
            output_parts.append(f"STDOUT:\n{stdout}")
        if stderr:
            output_parts.append(f"STDERR:\n{stderr}")

        if returncode == 0:
            output_parts.insert(0, "Command executed successfully")
        else:
            output_parts.insert(0, f"Command failed with exit code {returncode}")

        return tool_call_summary, "\n".join(output_parts)

    except Exception as e:
        return tool_call_summary, f"ERROR executing command: {str(e)}"
