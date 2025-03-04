from abc import ABCMeta
from enum import Enum
from pathlib import Path

from pydantic import BaseModel

from codemodder.logging import logger


class CaseInsensitiveEnum(str, Enum):
    @classmethod
    def _missing_(cls, value: object):
        if not isinstance(value, str):
            return super()._missing_(value)

        return cls.__members__.get(value.upper())


class CodeTFWriter(BaseModel, metaclass=ABCMeta):
    def write_report(self, outfile: Path | str) -> int:
        try:
            Path(outfile).write_text(self.model_dump_json(exclude_none=True))
        except Exception:
            logger.exception("failed to write report file.")
            # Any issues with writing the output file should exit status 2.
            return 2
        logger.debug("wrote report to %s", outfile)
        return 0
