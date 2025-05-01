from abc import ABCMeta
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict, model_validator

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


class Rule(BaseModel):
    id: str
    name: str
    url: Optional[str] = None

    model_config = ConfigDict(frozen=True)


class Finding(BaseModel):
    id: str
    rule: Rule

    model_config = ConfigDict(frozen=True)


class Action(CaseInsensitiveEnum):
    ADD = "add"
    REMOVE = "remove"


class PackageResult(CaseInsensitiveEnum):
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class DiffSide(CaseInsensitiveEnum):
    LEFT = "left"
    RIGHT = "right"


class PackageAction(BaseModel):
    action: Action
    result: PackageResult
    package: str


class Change(BaseModel):
    lineNumber: int
    description: Optional[str]
    diffSide: DiffSide = DiffSide.RIGHT
    properties: Optional[dict] = None
    packageActions: Optional[list[PackageAction]] = None

    @model_validator(mode="after")
    def validate_lineNumber(self):
        if self.lineNumber < 1:
            raise ValueError("lineNumber must be greater than 0")
        return self

    @model_validator(mode="after")
    def validate_description(self):
        if self.description is not None and not self.description:
            raise ValueError("description must not be empty")
        return self


class Rating(BaseModel):
    score: int
    description: Optional[str] = None


class FixQuality(BaseModel):
    safetyRating: Rating
    effectivenessRating: Rating
    cleanlinessRating: Rating
