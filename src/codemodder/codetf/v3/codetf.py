from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, model_validator

from codemodder.llm import TokenUsage
from codemodder.logging import logger

from ..common import Change, CodeTFWriter, Finding, FixQuality
from ..v2.codetf import AIMetadata as AIMetadatav2
from ..v2.codetf import ChangeSet as v2ChangeSet
from ..v2.codetf import CodeTF as CodeTFv2
from ..v2.codetf import Finding as v2Finding
from ..v2.codetf import Result
from ..v2.codetf import Run as Runv2


class Run(BaseModel):
    """Metadata about the analysis run that produced the results"""

    vendor: str
    tool: str
    version: str
    # optional free-form metadata about the project being analyzed
    # e.g. project name, directory, commit sha, etc.
    projectmetadata: dict | None = None
    # analysis duration in milliseconds
    elapsed: int | None = None
    # optional free-form metadata about the inputs used for the analysis
    # e.g. command line, environment variables, etc.
    inputmetadata: dict | None = None
    # optional free-form metadata about the analysis itself
    # e.g. timeouts, memory usage, etc.
    analysismetadata: dict | None = None


class FixStatusType(str, Enum):
    """Status of a fix"""

    fixed = "fixed"
    skipped = "skipped"
    failed = "failed"
    wontfix = "wontfix"


class FixStatus(BaseModel):
    """Metadata describing fix outcome"""

    status: FixStatusType
    reason: Optional[str] = None
    details: Optional[str] = None


class ChangeSet(BaseModel):
    path: str
    diff: str
    changes: list[Change] = []


class Reference(BaseModel):
    url: str
    description: Optional[str] = None

    @model_validator(mode="after")
    def validate_description(self):
        self.description = self.description or self.url
        return self


class Strategy(str, Enum):
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
    references: list[Reference] = []
    generation: GenerationMetadata


class FixResult(BaseModel):
    """Result corresponding to a single finding"""

    finding: Finding
    fixStatus: FixStatus
    changeSets: list[ChangeSet] = []
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

    def store_token_data(self, token_usage: TokenUsage):
        if token_usage == TokenUsage() or not self.fixMetadata:
            return

        if not self.fixMetadata.generation.ai:
            self.fixMetadata.generation.ai = AIMetadata(
                total_tokens=token_usage.total,
                completion_tokens=token_usage.completion_tokens,
                prompt_tokens=token_usage.prompt_tokens,
            )
        else:
            self.fixMetadata.generation.ai.completion_tokens = (
                self.fixMetadata.generation.ai.completion_tokens or 0
            ) + token_usage.completion_tokens
            self.fixMetadata.generation.ai.prompt_tokens = (
                self.fixMetadata.generation.ai.prompt_tokens or 0
            ) + token_usage.prompt_tokens
            self.fixMetadata.generation.ai.total_tokens = (
                self.fixMetadata.generation.ai.total_tokens or 0
            ) + token_usage.total


class CodeTF(CodeTFWriter, BaseModel):
    run: Run
    results: list[FixResult]


def from_v2_run(run: Runv2) -> Run:
    project_metadata = {"directory": run.directory} | (
        {"projectName": run.projectName} if run.projectName else {}
    )
    input_metadata = {"commandLine": run.commandLine} | (
        {"sarifs": run.sarifs} if run.sarifs else {}
    )

    return Run(
        vendor=run.vendor,
        tool=run.tool,
        version=run.version,
        elapsed=run.elapsed,
        projectmetadata=project_metadata,
        inputmetadata=input_metadata,
    )


def from_v2_aimetadata(ai_metadata: AIMetadatav2) -> AIMetadata:
    return AIMetadata(
        provider=ai_metadata.provider,
        models=[ai_metadata.model] if ai_metadata.model else None,
        total_tokens=ai_metadata.tokens,
        completion_tokens=ai_metadata.completion_tokens,
    )


def from_v2_result_per_finding(
    result: Result,
    strategy: Strategy | None = None,
    ai_metadata: AIMetadata | None = None,
    provisional: bool | None = None,
) -> FixResult | None:
    """
    This transformation assumes that the v2 result will only contain a single fixedFinding for all changesets.
    """

    changeset: v2ChangeSet | None = None
    finding: v2Finding | None = None
    # Find the changeset with a fixedFinding
    for cs in result.changeset:
        if cs.fixedFindings:
            changeset = cs
            finding = cs.fixedFindings[0]
            break
        else:
            # check each individual change
            for change in cs.changes:
                if change.fixedFindings:
                    changeset = cs
                    finding = change.fixedFindings[0]
                    break
    if changeset is None or finding is None:
        logger.debug("Either no changesets or fixed finding in the result")
        return None

    v3changesets = [
        ChangeSet(
            path=cs.path, diff=cs.diff, changes=[c.to_common() for c in cs.changes]
        )
        for cs in result.changeset
    ]

    # Generate the GenerationMetadata from the changeset if not passed as a parameter
    fix_result_strategy = strategy or (
        Strategy.ai if changeset.ai else Strategy.deterministic
    )
    fix_result_ai_metadata = ai_metadata or (
        from_v2_aimetadata(changeset.ai) if changeset.ai else None
    )
    fix_result_provisional = provisional or changeset.provisional or False

    generation_metadata = GenerationMetadata(
        strategy=fix_result_strategy,
        ai=fix_result_ai_metadata,
        provisional=fix_result_provisional,
    )

    fix_metadata = FixMetadata(
        id=result.codemod,
        summary=result.summary,
        description=result.description,
        generation=generation_metadata,
    )

    return FixResult(
        finding=Finding(**finding.model_dump()),
        fixStatus=FixStatus(status=FixStatusType.fixed),
        changeSets=v3changesets,
        fixMetadata=fix_metadata,
    )


def from_v2_result(result: Result) -> list[FixResult]:
    fix_results: list[FixResult] = []
    # generate fixed
    for cs in result.changeset:
        # No way of identifying hybrid AI codemods by the metadata alone
        generation_metadata = GenerationMetadata(
            strategy=Strategy.ai if cs.ai else Strategy.deterministic,
            ai=from_v2_aimetadata(cs.ai) if cs.ai else None,
            provisional=False,
        )
        for c in cs.changes:
            for f in c.fixedFindings or []:
                fix_metadata = FixMetadata(
                    id=result.codemod,
                    summary=result.summary,
                    description=result.description,
                    generation=generation_metadata,
                )
                # Retrieve diff from changeset since individual diffs per change may not exist
                # If the codetf was generated with per-finding, each ChangeSet will have a single change anyway
                changeset = ChangeSet(
                    path=cs.path, diff=cs.diff, changes=[c.to_common()]
                )
                fix_results.append(
                    FixResult(
                        finding=Finding(**f.model_dump()),
                        fixStatus=FixStatus(status=FixStatusType.fixed),
                        changeSets=[changeset],
                        fixMetadata=fix_metadata,
                    )
                )

    # generate unfixed
    for f in result.unfixedFindings or []:
        fix_results.append(
            FixResult(
                finding=Finding(**f.model_dump()),
                fixStatus=FixStatus(status=FixStatusType.failed, reason=f.reason),
            )
        )

    return fix_results


def from_v2(codetf: CodeTFv2) -> CodeTF:
    return CodeTF(
        run=from_v2_run(codetf.run),
        results=[fr for result in codetf.results for fr in from_v2_result(result)],
    )
