import logging

from rich.console import Console
from rich.logging import RichHandler

# A single shared console so that log lines and progress bars cooperate
# (Rich renders logs above a live progress bar when they share a console).
console = Console()


def setup_logging(debug: bool = False) -> None:
    """Configure color logging through Rich.

    When ``debug`` is set, every logger drops to ``DEBUG`` for maximum
    verbosity. Otherwise the level is ``INFO``: the chatty per-track/per-album
    messages (logged at ``DEBUG``) stay hidden so the progress bar is the only
    thing on screen, while warnings and errors still get through.
    """
    level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                console=console,
                rich_tracebacks=True,
                show_path=debug,
                markup=True,
            )
        ],
    )

    # Keep third-party libraries quiet unless we explicitly want everything.
    if not debug:
        for noisy in ("urllib3", "requests", "chardet", "charset_normalizer"):
            logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
