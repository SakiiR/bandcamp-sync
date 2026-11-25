# Development

This page tells you how to work on the code.

## Set up the environment

1. Install `uv`. See [Installation](installation.md).
2. Run this command to install the dependencies and the development tools:

```
uv sync
```

The command installs `pytest`, `ruff` and `ty` from the development group.

## The project layout

| Path | Content |
| --- | --- |
| `main.py` | The command-line interface and the sync logic. |
| `bandcamp_sync/downloader.py` | The HTTP client, the downloads and the rate limit control. |
| `bandcamp_sync/album.py` | The album and track data models. |
| `bandcamp_sync/page.py` | The parser for a Bandcamp page. |
| `bandcamp_sync/slugify.py` | The function that makes a safe file name. |
| `bandcamp_sync/log.py` | The log setup. |
| `bandcamp_sync/exceptions.py` | The error classes. |
| `tests/` | The tests. |

## Run the program

Run the program from the source code:

```
uv run main.py --help
```

## Run the tests

The project uses `pytest`. The tests are in the `tests` folder.

Run all tests:

```
uv run pytest
```

Run one test file:

```
uv run pytest tests/test_slugify.py
```

## Check the code

### Lint

The project uses `ruff` for the lint checks.

Check the code:

```
uv run ruff check
```

Fix the problems that `ruff` can fix:

```
uv run ruff check --fix
```

Format the code:

```
uv run ruff format
```

### Types

The project uses `ty` for the type checks.

Check the types:

```
uv run ty check
```

## Before you commit

Do these checks before you commit:

1. Run `uv run pytest`.
2. Run `uv run ruff check`.
3. Run `uv run ty check`.

Commit only when all checks pass.

## The HTTP client

The program uses `httpx` with the async client. The downloader methods are
async. The command functions use `asyncio.run` to start the async code.

Keep new network code async. Use `await` for each request.
