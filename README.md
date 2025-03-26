# minicline

Command-line interface for performing software engineering tasks using large language models. It is based on Cline, but is simpler, uses fewer input tokens, has fewer capabilities, and does not depend on VSCode. It borrows a lot of the same prompts, logic, and formatting as Cline.

## Installation

```bash
pip install -e .
```

## Usage

From command line:
```bash
# Provide instructions directly
minicline perform-task "your instructions here"

# Or use a file containing instructions
minicline perform-task -f /path/to/instructions.txt
```

From Python:
```python
from minicline import perform_task

instructions = '...'

perform_task(instructions, cwd="/path/to/working/directory")

## License

This project is licensed under the Apache 2.0 License.
