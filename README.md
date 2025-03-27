# minicline

Command-line and Python interface for performing software engineering tasks using large language models. It is based on [Cline](https://cline.bot/), but is simpler, uses fewer input tokens, has fewer capabilities, and does not depend on VSCode. It borrows prompts, logic, conventions, and formatting from Cline.

The primary focus is automatic generation of scientific notebooks, targeting projects like [dandi-notebook-gen](https://github.com/magland/dandi-notebook-gen).

## Installation

```bash
# clone this repo, then
cd minicline
pip install .
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

## Automation Options

The CLI supports two automation flags that can streamline task execution:

* `--auto`: Enables automatic mode where no user input is required. The AI will proceed with all actions without asking for confirmation, except for commands that require approval (unless `--approve-all-commands` is also set).

* `--approve-all-commands`: Automatically approves all commands that would normally require manual approval. This includes potentially impactful operations like installing packages, modifying system files, or running network operations.

Use these options with caution, especially in production environments, as they bypass normal safety prompts and confirmations.
```
## License

This project is licensed under the Apache 2.0 License.
