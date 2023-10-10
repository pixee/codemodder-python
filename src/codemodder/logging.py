from enum import Enum
import logging
import sys

logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger("codemodder")


class OutputFormat(Enum):
    """
    Enum for the output format of the logger.
    """

    HUMAN = "human"
    JSON = "json"


def configure_logger(verbose: bool):
    """
    Configure the logger based on the verbosity level.
    """
    # TODO: eventually process human/json here
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
