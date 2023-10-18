from enum import Enum
import logging
import sys

logger = logging.getLogger("codemodder")


class OutputFormat(Enum):
    """
    Enum for the output format of the logger.
    """

    HUMAN = "human"
    JSON = "json"

    def __str__(self):
        """For rendering properly in argparse help."""
        return self.value.lower()


def log_section(section_name: str):
    """
    Log a section header.
    """
    logger.info("\n[%s]", section_name)


def log_list(level: int, header: str, items: list, predicate=None):
    """
    Log a list of items.
    """
    logger.log(level, "%s:", header)
    for item in items:
        logger.log(level, "  - %s", predicate(item) if predicate else item)


def configure_logger(verbose: bool):
    """
    Configure the logger based on the verbosity level.
    """
    log_level = logging.DEBUG if verbose else logging.INFO

    # TODO: this should all be conditional on the output format
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(log_level)
    stdout_handler.addFilter(lambda record: record.levelno <= logging.WARNING)

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.ERROR)

    logging.basicConfig(
        format="%(message)s",
        level=log_level,
        handlers=[stdout_handler, stderr_handler],
    )
