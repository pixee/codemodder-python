"""
Data models for the CodeTF format.

We need to keep this in sync with the CodeTF schema.
"""

from __future__ import annotations

import os
import sys
from enum import Enum
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, model_validator

from codemodder import __version__
from codemodder.logging import logger

if TYPE_CHECKING:
    from codemodder.context import CodemodExecutionContext


class Action(Enum):
    ADD = "add"
    REMOVE = "remove"


class PackageResult(Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class DiffSide(Enum):
    LEFT = "left"
    RIGHT = "right"


class PackageAction(BaseModel):
    action: Action
    result: PackageResult
    package: str


class Change(BaseModel):
    lineNumber: int
    description: Optional[str]
    # All of our changes are currently treated as additive, so it makes sense
    # for the comments to appear on the RIGHT side of the split diff. Eventually we
    # may want to differentiate between LEFT and RIGHT, but for now we'll just
    # default to RIGHT.
    diffSide: DiffSide = DiffSide.RIGHT
    properties: Optional[dict] = None
    packageActions: Optional[list[PackageAction]] = None
    findings: Optional[list[Finding]] = None

    @model_validator(mode="after")
    def validate_lineNumber(self):
        if self.lineNumber < 1:
            raise ValueError("lineNumber must be greater than 0")
        return self


class AIMetadata(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    tokens: Optional[int] = None


class ChangeSet(BaseModel):
    """A set of changes made to a file at `path`"""

    path: str
    diff: str
    changes: list[Change] = []
    ai: Optional[AIMetadata] = None


class Reference(BaseModel):
    url: str
    description: Optional[str] = None

    @model_validator(mode="after")
    def validate_description(self):
        self.description = self.description or self.url
        return self


class Rule(BaseModel):
    id: str
    name: str
    url: Optional[str] = None


class Finding(BaseModel):
    id: str
    rule: Rule

    def to_unfixed_finding(
        self,
        *,
        path: str,
        line_number: Optional[int] = None,
        reason: str,
    ) -> UnfixedFinding:
        return UnfixedFinding(
            id=self.id,
            rule=self.rule,
            path=path,
            lineNumber=line_number,
            reason=reason,
        )


class UnfixedFinding(Finding):
    path: str
    lineNumber: Optional[int] = None
    reason: str


class DetectionTool(BaseModel):
    name: str


class Result(BaseModel):
    codemod: str
    summary: str
    description: str
    detectionTool: Optional[DetectionTool] = None
    references: Optional[list[Reference]] = None
    properties: Optional[dict] = None
    failedFiles: Optional[list[str]] = None
    changeset: list[ChangeSet]
    unfixedFindings: Optional[list[UnfixedFinding]] = None


class Sarif(BaseModel):
    artifact: str
    sha1: str


class Run(BaseModel):
    vendor: str
    tool: str
    version: str
    projectName: Optional[str] = None
    commandLine: str
    elapsed: Optional[int]
    directory: str
    sarifs: list[Sarif] = []


class CodeTF(BaseModel):
    run: Run
    results: list[Result]

    @classmethod
    def build(
        cls,
        context: CodemodExecutionContext,
        elapsed_ms,
        original_args,
        results: list[Result],
    ):
        command_name = os.path.basename(sys.argv[0])
        command_args = " ".join(original_args)
        run = Run(
            vendor="pixee",
            tool="codemodder-python",
            version=__version__,
            projectName=None,
            commandLine=f"{command_name} {command_args}",
            elapsed=elapsed_ms,
            directory=str(context.directory.absolute()),
            # TODO: this should be populated from the context
            sarifs=[],
        )
        return cls(run=run, results=results)

    def write_report(self, outfile):
        try:
            with open(outfile, "w", encoding="utf-8") as f:
                f.write(self.model_dump_json(exclude_none=True))
        except Exception:
            logger.exception("failed to write report file.")
            # Any issues with writing the output file should exit status 2.
            return 2
        logger.debug("wrote report to %s", outfile)
        return 0
