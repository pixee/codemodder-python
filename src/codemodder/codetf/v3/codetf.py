from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, model_validator

from ..common import CaseInsensitiveEnum, CodeTFWriter


class Run(BaseModel):
    """Metadata about the analysis run that produced the results"""

    vendor: str
    tool: str
    version: str
    # Optional free-form metadata about the project being analyzed
    # e.g. project name, directory, commit SHA, etc.
    projectMetadata: Optional[str] = None
    # Analysis duration in milliseconds
    elapsed: Optional[int] = None
    # Optional free-form metadata about the inputs used for the analysis
    # e.g. command line, environment variables, etc.
    inputMetadata: Optional[dict] = None
    # Optional free-form metadata about the analysis itself
    # e.g. timeouts, memory usage, etc.
    analysisMetadata: Optional[dict] = None


class FixStatusType(str, Enum):
    """Status of a fix"""

    fixed = "fixed"
    skipped = "skipped"
    failed = "failed"
    wontfix = "wontfix"


class FixStatus(BaseModel):
    """Metadata describing fix outcome"""

    status: FixStatusType
    reason: Optional[str]
    details: Optional[str]


class Rule(BaseModel):
    id: str
    name: str
    url: Optional[str] = None


class Finding(BaseModel):
    id: str
    rule: Optional[Rule] = None


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


class ChangeSet(BaseModel):
    path: str
    diff: str
    changes: list[Change]


class Reference(BaseModel):
    url: str
    description: Optional[str] = None

    @model_validator(mode="after")
    def validate_description(self):
        self.description = self.description or self.url
        return self


class Strategy(Enum):
    ai = "ai"
    hybrid = "hybrid"
    deterministic = "deterministic"


class AIMetadata(BaseModel):
    provider: Optional[str] = None
    models: Optional[list[str]] = None
    total_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    prompt_tokens: Optional[int] = None


class GenerationMetadata(BaseModel):
    strategy: Strategy
    ai: Optional[AIMetadata] = None
    provisional: bool


class FixMetadata(BaseModel):
    # Fix provider ID, corresponds to legacy codemod ID
    id: str
    # A brief summary of the fix
    summary: str
    # A detailed description of the fix
    description: str
    references: list[Reference]
    generation: GenerationMetadata


class Rating(BaseModel):
    score: int
    description: Optional[str] = None


class FixQuality(BaseModel):
    safetyRating: Rating
    effectivenessRating: Rating
    cleanlinessRating: Rating


class FixResult(BaseModel):
    """Result corresponding to a single finding"""

    finding: Finding
    fixStatus: FixStatus
    changeSets: list[ChangeSet]
    fixMetadata: Optional[FixMetadata] = None
    fixQuality: Optional[FixQuality] = None
    # A description of the reasoning process that led to the fix
    reasoningSteps: Optional[list[str]] = None

    @model_validator(mode="after")
    def validate_fixMetadata(self):
        if self.fixStatus.status == FixStatusType.fixed:
            if not self.changeSets:
                raise ValueError("changeSets must be provided for fixed results")
            if not self.fixMetadata:
                raise ValueError("fixMetadata must be provided for fixed results")
        return self


class CodeTF(CodeTFWriter, BaseModel):
    run: Run
    results: list[FixResult]
