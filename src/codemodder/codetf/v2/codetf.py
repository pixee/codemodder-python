"""
Data models for the CodeTF format.

We need to keep this in sync with the CodeTF schema.
"""

from __future__ import annotations

import os
import sys
from enum import Enum
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, model_validator

from codemodder import __version__

from ..common import CaseInsensitiveEnum, CodeTFWriter

if TYPE_CHECKING:
    from codemodder.context import CodemodExecutionContext


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
    # All of our changes are currently treated as additive, so it makes sense
    # for the comments to appear on the RIGHT side of the split diff. Eventually we
    # may want to differentiate between LEFT and RIGHT, but for now we'll just
    # default to RIGHT.
    diffSide: DiffSide = DiffSide.RIGHT
    properties: Optional[dict] = None
    packageActions: Optional[list[PackageAction]] = None
    fixedFindings: Optional[list[Finding]] = None

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

    def with_findings(self, findings: list[Finding] | None) -> Change:
        return Change(
            lineNumber=self.lineNumber,
            description=self.description,
            diffSide=self.diffSide,
            properties=self.properties,
            packageActions=self.packageActions,
            fixedFindings=findings,
        )


class AIMetadata(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    prompt_tokens: Optional[int] = None


class Strategy(Enum):
    ai = "ai"
    hybrid = "hybrid"
    deterministic = "deterministic"


class Rating(BaseModel):
    score: int
    description: Optional[str] = None


class FixQuality(BaseModel):
    safetyRating: Rating
    effectivenessRating: Rating
    cleanlinessRating: Rating


class ChangeSet(BaseModel):
    """A set of changes made to a file at `path`"""

    path: str
    diff: str
    changes: list[Change] = []
    ai: Optional[AIMetadata] = None
    strategy: Optional[Strategy] = None
    provisional: Optional[bool] = False
    # For fixed findings that are not associated with a specific change
    fixedFindings: Optional[list[Finding]] = None
    fixQuality: Optional[FixQuality] = None

    def with_changes(self, changes: list[Change]) -> ChangeSet:
        return ChangeSet(
            path=self.path,
            diff=self.diff,
            changes=changes,
            ai=self.ai,
            strategy=self.strategy,
            provisional=self.provisional,
            fixedFindings=self.fixedFindings,
        )


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

    model_config = ConfigDict(frozen=True)


class Finding(BaseModel):
    id: Optional[str] = None
    rule: Rule

    model_config = ConfigDict(frozen=True)

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

    def with_rule(self, name: str, url: Optional[str]) -> Finding:
        return Finding(
            id=self.id,
            rule=Rule(id=self.rule.id, name=name, url=url),
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


class CodeTF(CodeTFWriter, BaseModel):
    run: Run
    results: list[Result]

    @classmethod
    def build(
        cls,
        context: CodemodExecutionContext,
        elapsed_ms,
        original_args: list,
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
