"""Docker container management for persistent containers."""

import os
import subprocess
import time
import json
from typing import Optional, Dict, Any
from pathlib import Path

class DockerManager:
    """Manages persistent Docker containers for minicline."""

    def __init__(self, cwd: str):
        self.cwd = cwd
        self.use_apptainer = os.getenv("MINICLINE_USE_APPTAINER", "false").lower() == "true"

    def start_container(self, image: str, container_name: Optional[str] = None) -> str:
        """Start a new persistent Docker container.

        Args:
            image: Docker image to use
            container_name: Optional container name, if not provided will generate one

        Returns:
            Container name
        """
        if self.use_apptainer:
            raise NotImplementedError("Persistent containers not supported with Apptainer")

        if not container_name:
            container_name = f"minicline_persistent_{int(time.time())}"

        # Check if container already exists
        try:
            result = subprocess.run(
                ["docker", "inspect", container_name],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                # Container exists, check if it's running
                container_info = json.loads(result.stdout)[0]
                if container_info["State"]["Running"]:
                    print(f"Container {container_name} is already running")
                    return container_name
                else:
                    # Container exists but not running, start it
                    subprocess.run(["docker", "start", container_name], check=True)
                    print(f"Started existing container: {container_name}")
                    return container_name
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
            pass  # Container doesn't exist or error checking, proceed to create

        # Pull the image first
        print(f"Pulling Docker image: {image}")
        subprocess.run(["docker", "pull", image], check=True)

        # Create and start the container
        docker_cmd = [
            "docker", "run",
            "-d",  # Run in detached mode
            "--name", container_name,
            "-v", f"{self.cwd}:{self.cwd}",  # Mount current directory
            "-w", self.cwd,  # Set working directory
            "-t",  # Allocate a pseudo-TTY
            image,
            "sleep", "infinity"  # Keep container running
        ]

        subprocess.run(docker_cmd, check=True)
        print(f"Started new container: {container_name}")
        return container_name

    def stop_container(self, container_name: str) -> bool:
        """Stop and remove a Docker container.

        Args:
            container_name: Name of container to stop

        Returns:
            True if successful, False otherwise
        """
        if self.use_apptainer:
            print("No persistent containers to stop with Apptainer")
            return True

        try:
            # Stop the container
            subprocess.run(["docker", "stop", container_name], check=True)
            # Remove the container
            subprocess.run(["docker", "rm", container_name], check=True)
            print(f"Stopped and removed container: {container_name}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error stopping container {container_name}: {e}")
            return False

    def list_containers(self) -> Dict[str, Dict[str, Any]]:
        """List all minicline containers.

        Returns:
            Dictionary mapping container names to their info
        """
        if self.use_apptainer:
            return {}

        try:
            result = subprocess.run(
                ["docker", "ps", "-a", "--filter", "name=minicline_", "--format", "json"],
                capture_output=True,
                text=True,
                check=True
            )

            containers = {}
            for line in result.stdout.strip().split('\n'):
                if line:
                    container_info = json.loads(line)
                    containers[container_info["Names"]] = {
                        "status": container_info["State"],
                        "image": container_info["Image"],
                        "created": container_info["CreatedAt"]
                    }
            return containers
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return {}

    def execute_in_container(self, container_name: str, command: str) -> subprocess.Popen:
        """Execute a command in an existing container.

        Args:
            container_name: Name of container to execute in
            command: Command to execute

        Returns:
            Popen process object
        """
        if self.use_apptainer:
            raise NotImplementedError("Persistent containers not supported with Apptainer")

        docker_cmd = [
            "docker", "exec",
            "-i",  # Interactive
            "-w", self.cwd,  # Set working directory
            container_name,
            "/bin/sh", "-c", command
        ]

        return subprocess.Popen(
            docker_cmd,
            shell=False,
            cwd=self.cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Create new process group
        )

    def container_exists(self, container_name: str) -> bool:
        """Check if a container exists and is running.

        Args:
            container_name: Name of container to check

        Returns:
            True if container exists and is running, False otherwise
        """
        if self.use_apptainer:
            return False

        try:
            result = subprocess.run(
                ["docker", "inspect", container_name],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                container_info = json.loads(result.stdout)[0]
                return container_info["State"]["Running"]
            return False
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
            return False
