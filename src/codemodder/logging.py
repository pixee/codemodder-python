import logging
import sys
from enum import Enum
from typing import Optional

from pythonjsonlogger import jsonlogger

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


class CodemodderJsonFormatter(jsonlogger.JsonFormatter):
    project_name: Optional[str]

    def __init__(self, *args, project_name: Optional[str] = None, **kwargs):
        self.project_name = project_name
        super().__init__(*args, **kwargs)

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = log_record.pop("asctime")
        log_record.move_to_end("timestamp", last=False)
        log_record["level"] = record.levelname.upper()
        log_record["file"] = record.filename
        log_record["line"] = record.lineno
        if self.project_name:
            log_record["project-name"] = self.project_name


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


def configure_logger(
    verbose: bool, log_format: OutputFormat, project_name: Optional[str] = None
):
    """
    Configure the logger based on the verbosity level.
    """
    log_level = logging.DEBUG if verbose else logging.INFO

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(log_level)
    handlers = [stdout_handler]

    match log_format:
        case OutputFormat.HUMAN:
            stdout_handler.addFilter(lambda record: record.levelno <= logging.WARNING)
            stderr_handler = logging.StreamHandler(sys.stderr)
            stderr_handler.setLevel(logging.ERROR)
            handlers.append(stderr_handler)
        case OutputFormat.JSON:
            formatter = CodemodderJsonFormatter(
                "%(asctime) %(level) %(message) %(file) %(line)",
                project_name=project_name,
            )
            stdout_handler.setFormatter(formatter)

    logging.basicConfig(
        format="%(message)s",
        level=log_level,
        handlers=handlers,
    )
