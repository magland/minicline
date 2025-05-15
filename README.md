# minicline

Command-line and Python interface for performing software engineering tasks using large language models. It is based on [Cline](https://cline.bot/), but is simpler, uses fewer input tokens, has fewer capabilities, and does not depend on VSCode. It borrows prompts, logic, conventions, and formatting from Cline.

This package was created during the [Pre-COSYNE Brainhack](https://pre-cosyne-brainhack.github.io/hackathon2025/posts/about/), March 2025, Montreal.

The primary focus is automatic generation of scientific notebooks, targeting projects like [dandi-notebook-gen](https://github.com/magland/dandi-notebook-gen).

## Installation

```bash
pip install minicline
```

## Setup

The application requires the `OPENROUTER_API_KEY` environment variable to be set. You can set this variable by creating a `.env` file in the working directory with the following content:

```
OPENROUTER_API_KEY=your_api_key
```

## Usage

From command line:
```bash
# Provide instructions directly
minicline perform-task "your instructions here"

# Specify a model
minicline perform-task --model google/gemini-2.0-flash-001 "your instructions here"

# Use a file containing instructions
minicline perform-task -f /path/to/instructions.txt

# Run in automatic mode (no user input required except for executing commands that are deemed to require user approval)
minicline perform-task --auto "your instructions here"

# Automatically approve all commands that are deemed require user approval
minicline perform-task --auto --approve-all-commands "your instructions here"
```

From Python:
```python
from minicline import perform_task

instructions = '...'

# Default model (google/gemini-2.0-flash-001)
perform_task(instructions, cwd="/path/to/working/directory")

# Specify a different OpenRouter model
perform_task(instructions, cwd="/path/to/working/directory", model="...")

# Run in automatic mode (see above)
perform_task(instructions, cwd="/path/to/working/directory", auto=True)

# Automatically approve all commands (see above)
perform_task(instructions, cwd="/path/to/working/directory", auto=True, approve_all_commands=True)
```

## Working Directory

MiniCline performs all operations within a specified working directory. File paths and commands are interpreted relative to this directory. When using the CLI, the working directory defaults to the current directory. When using the Python API, specify the working directory using the `cwd` parameter.

## Automation and Security Options

The CLI supports various flags and environment variables that control task execution and security:

### Command Execution Modes

* `--auto`: Enables automatic mode where no user input is required. The AI will proceed with all actions without asking for confirmation, except for commands that require approval (unless `--approve-all-commands` is also set).

* `--approve-all-commands`: Automatically approves all commands that would normally require manual approval. This includes potentially impactful operations like installing packages, modifying system files, or running network operations.

### Container Security

By default, minicline executes commands within a container for security. This prevents unauthorized access to the host system while maintaining a controlled environment:

* Commands run inside the container can only access files in the current working directory, as this is the only directory mounted from the host system
* minicline itself can read and write files outside the container, but only within the current working directory
* File system isolation prevents commands from accessing sensitive host system files
* The `--no-container` flag disables container usage and runs commands directly on the host system. This option is dangerous and should be used with extreme caution, especially when combined with `--auto` or `--approve-all-commands`

### Environment Variables

* `MINICLINE_DOCKER_IMAGE`: Specifies the Docker image to use for command execution. Defaults to `jupyter/scipy-notebook:latest`.

* `MINICLINE_USE_APPTAINER`: Set to "true" to use Apptainer (formerly Singularity) instead of Docker for containerization.

Use these options with caution, especially in production environments, as they can affect system security and bypass normal safety prompts and confirmations.

## Some notes about changes to the system prompt relative to Cline

In auto mode, don't provide instructions for ask_followup_question as it will be ignored.

Updated the "Tool Use Formatting" to be explicit about using the <thinking></thinking> tags because I found that some models didn't make use of that.

Removed all MCP functionality.

Support read_image in addition to read_file.

## License

This project is licensed under the Apache 2.0 License.
