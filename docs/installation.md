# Installation

This page tells you how to install Bandcamp Sync.

## Requirements

- Python 3.13 or higher.
- The `uv` package manager.

The program uses `uv` for the dependencies and the virtual environment. You do
not install the packages by hand.

## Run without an install

`uvx` is part of `uv`. It downloads the program, runs it and then removes it.
You do not install the program first.

Run the program from the Git repository:

```
uvx --from git+https://github.com/SakiiR/bandcamp-sync.git bandcamp-sync --help
```

This method is the easiest way to use the program. The steps below are for a
local install from the source code.

## Install uv

`uv` is a fast package manager for Python.

On Linux or macOS, run this command:

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

On Windows, run this command in PowerShell:

```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

For other methods, see the `uv` documentation.

## Install the dependencies

1. Open a terminal in the project folder.
2. Run this command:

```
uv sync
```

The command does these actions:

- It reads the dependencies from `pyproject.toml`.
- It uses the exact versions from `uv.lock`.
- It makes a virtual environment in the `.venv` folder.
- It installs all packages into that environment.

## Test the installation

Run this command:

```
uv run main.py --help
```

The command shows the list of commands. The installation is correct when you
see this list.

## Next step

Go to [Usage](usage.md) to run your first command.
