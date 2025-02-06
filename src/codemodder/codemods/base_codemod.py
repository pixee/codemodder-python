from __future__ import annotations

import functools
import importlib.resources
from abc import ABCMeta, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property
from importlib.abc import Traversable
from pathlib import Path

from codemodder.code_directory import file_line_patterns
from codemodder.codemods.base_detector import BaseDetector
from codemodder.codemods.base_transformer import BaseTransformerPipeline
from codemodder.codemods.semgrep import SemgrepRuleDetector
from codemodder.codetf import DetectionTool, Reference
from codemodder.context import CodemodExecutionContext
from codemodder.file_context import FileContext
from codemodder.llm import TokenUsage
from codemodder.logging import logger
from codemodder.result import ResultSet


class ReviewGuidance(Enum):
    MERGE_AFTER_REVIEW = 1
    MERGE_AFTER_CURSORY_REVIEW = 2
    MERGE_WITHOUT_REVIEW = 3


@dataclass
class Metadata:
    name: str
    summary: str
    review_guidance: ReviewGuidance
    references: list[Reference] = field(default_factory=list)
    description: str | None = None
    tool: ToolMetadata | None = None
    language: str = "python"


@dataclass
class ToolRule:
    id: str
    name: str
    url: str | None = None


@dataclass
class ToolMetadata:
    name: str
    rules: list[ToolRule]

    @property
    def rule_ids(self):
        return [rule.id for rule in self.rules]


class BaseCodemod(metaclass=ABCMeta):
    """
    Base class for all codemods

    Conceptually a codemod is composed of the following attributes:
    * Metadata: contains information about the codemod including its name, summary, and review guidance
    * Detector (optional): the source of results indicating which code locations the codemod should be applied
    * Transformer: a transformer pipeline that will be applied to each applicable file and perform the actual modifications

    A detector may parse result files generated by other tools or it may
    perform its own analysis at runtime, potentially by calling another tool
    (e.g. Semgrep).

    Some codemods may not require a detector if the transformation pipeline
    itself is capable of determining locations to modify.

    Codemods that apply the same transformation but use different detectors
    should be implemented as distinct codemod classes.
    """

    _metadata: Metadata
    detector: BaseDetector | None
    transformer: BaseTransformerPipeline
    default_extensions: list[str] | None
    provider: str | None

    def __init__(
        self,
        *,
        metadata: Metadata,
        detector: BaseDetector | None = None,
        transformer: BaseTransformerPipeline,
        default_extensions: list[str] | None = None,
        provider: str | None = None,
    ):
        # Metadata should only be accessed via properties
        self._metadata = metadata
        self.detector = detector
        self.transformer = transformer
        self.default_extensions = default_extensions or [".py"]
        self.provider = provider

    @property
    @abstractmethod
    def origin(self) -> str: ...

    @property
    @abstractmethod
    def docs_module_path(self) -> str: ...

    @property
    def name(self) -> str:
        """Non-unique property for codemods. Multiple codemods can have the same name."""
        return self._metadata.name

    @property
    def language(self) -> str:
        return self._metadata.language

    @property
    def id(self) -> str:
        return f"{self.origin}:{self.language}/{self.name}"

    @property
    def summary(self):
        return self._metadata.summary

    @property
    def detection_tool(self) -> DetectionTool | None:
        if self._metadata.tool is None:
            return None

        return DetectionTool(
            name=self._metadata.tool.name,
        )

    @property
    def detection_tool_rules(self) -> list[ToolRule]:
        return self._metadata.tool.rules if self._metadata.tool else []

    @cached_property
    def docs_module(self) -> Traversable:
        return importlib.resources.files(self.docs_module_path)

    @cached_property
    def description(self) -> str:
        if self._metadata.description is None:
            doc_path = self.docs_module / f"{self.origin}_python_{self.name}.md"
            return doc_path.read_text()
        return self._metadata.description

    @property
    def review_guidance(self):
        return self._metadata.review_guidance.name.replace("_", " ").title()

    @property
    def references(self) -> list[Reference]:
        return self._metadata.references

    def describe(self):
        return {
            "codemod": self.id,
            "summary": self.summary,
            "description": self.description,
            "references": [ref.model_dump() for ref in self.references],
        }

    @property
    def _internal_name(self) -> str:
        """Used only for internal semgrep runs."""
        # Unfortunately the IDs from semgrep are not fully specified
        # TODO: eventually we need to be able to use fully specified IDs here
        return self.name

    @abstractmethod
    def get_files_to_analyze(
        self,
        context: CodemodExecutionContext,
        results: ResultSet | None,
    ) -> list[Path]:
        """
        Get the list of files to analyze

        This method is responsible for determining the list of files that should be analyzed by the codemod.

        This method should return a list of `Path` objects representing the files to analyze.
        """
        ...

    def _apply(
        self,
        context: CodemodExecutionContext,
        rules: list[str],
    ) -> None | TokenUsage:
        if self.provider and (
            not (provider := context.providers.get_provider(self.provider))
            or not provider.is_available
        ):
            logger.warning(
                "provider %s is not available, skipping codemod", self.provider
            )
            return None

        if isinstance(self.detector, SemgrepRuleDetector):
            if (
                context.semgrep_prefilter_results
                and self._internal_name
                not in context.semgrep_prefilter_results.all_rule_ids()
            ):
                logger.debug(
                    "no results from semgrep for %s, skipping analysis",
                    self.id,
                )
                return None

        results: ResultSet | None = (
            # It seems like semgrep doesn't like our fully-specified id format so pass in short name instead.
            self.detector.apply(self._internal_name, context)
            if self.detector
            else None
        )

        if results is not None and not results:
            logger.debug("No results for %s", self.id)
            return None

        if not (files_to_analyze := self.get_files_to_analyze(context, results)):
            logger.debug("No files matched for %s", self.id)
            return None

        process_file = functools.partial(
            self._process_file, context=context, results=results, rules=rules
        )

        contexts = []
        if context.max_workers == 1:
            logger.debug("processing files serially")
            contexts.extend([process_file(file) for file in files_to_analyze])
        else:
            with ThreadPoolExecutor() as executor:
                logger.debug("using executor with %s workers", context.max_workers)
                contexts.extend(executor.map(process_file, files_to_analyze))
                executor.shutdown(wait=True)

        context.process_results(self.id, contexts)
        return None

    def apply(self, context: CodemodExecutionContext) -> None | TokenUsage:
        """
        Apply the codemod with the given codemod execution context

        This method is responsible for orchestrating the application of the codemod to a given list of files.

        It will first apply the detector (if any) to the files to determine which files should be modified.

        It then applies the transformer pipeline to each file applicable file, potentially generating a change set.

        All results are then processed and reported to the context.

        Per-file processing can be parallelized based on the `max_workers` setting.

        :param context: The codemod execution context
        """
        return self._apply(context, [self._internal_name])

    def _process_file(
        self,
        filename: Path,
        context: CodemodExecutionContext,
        results: ResultSet | None,
        rules: list[str],
    ):
        line_exclude = file_line_patterns(filename, context.path_exclude)
        line_include = file_line_patterns(filename, context.path_include)
        findings_for_rule = None
        if results is not None:
            findings_for_rule = []
            for rule in rules:
                findings_for_rule.extend(
                    results.results_for_rule_and_file(context, rule, filename)
                )
            logger.debug("%d findings for %s", len(findings_for_rule), filename)

        file_context = FileContext(
            context.directory,
            filename,
            line_exclude,
            line_include,
            findings_for_rule,
        )
        if results is not None and not findings_for_rule:
            logger.debug("no findings for %s, short-circuiting analysis", filename)
            return file_context

        if change_set := self.transformer.apply(
            context, file_context, findings_for_rule
        ):
            file_context.add_changeset(change_set)

        return file_context

    def __repr__(self) -> str:
        return f"{self.id}"


class FindAndFixCodemod(BaseCodemod, metaclass=ABCMeta):
    """
    Base class for codemods that find and fix issues in code
    """

    def get_files_to_analyze(
        self,
        context: CodemodExecutionContext,
        results: ResultSet | None,
    ) -> list[Path]:
        """
        Determine which files to analyze based on find-and-fix paths

        Using `context.find_and_fix_paths` automatically accounts for any user-provided `path_include` and `path_exclude` settings
        as well as defaults for find-and-fix codemods, so there's no need for additional filtering logic.
        """
        del results
        return (
            [
                path
                for path in context.find_and_fix_paths
                if path.suffix in self.default_extensions
            ]
            if self.default_extensions
            else context.find_and_fix_paths
        )


class RemediationCodemod(BaseCodemod, metaclass=ABCMeta):
    """
    Base class for codemods that apply remediations to code
    """

    requested_rules: list[str]

    def __init__(
        self,
        *,
        metadata: Metadata,
        detector: BaseDetector | None = None,
        transformer: BaseTransformerPipeline,
        default_extensions: list[str] | None = None,
        requested_rules: list[str] | None = None,
        provider: str | None = None,
    ):
        super().__init__(
            metadata=metadata,
            detector=detector,
            transformer=transformer,
            default_extensions=default_extensions,
            provider=provider,
        )
        self.requested_rules = []
        if requested_rules:
            self.requested_rules.extend(requested_rules)

    def apply(self, context: CodemodExecutionContext) -> None | TokenUsage:
        return self._apply(context, self.requested_rules)

    def get_files_to_analyze(
        self,
        context: CodemodExecutionContext,
        results: ResultSet | None,
    ) -> list[Path]:
        """
        Get the list of files to analyze based on which files have findings associated with the requested rules

        Using `context.files_to_analyze` includes all files in the directory. These paths are filtered by locations that are
        associated with findings for the requested rules. Finally these paths are filtered according to user-provided `path_include`
        and `path_exclude` settings using `context.filter_paths`.
        """
        return context.filter_paths(
            [
                path
                for path in context.files_to_analyze
                if path.suffix in (self.default_extensions or [])
                and any(
                    results.results_for_rule_and_file(context, rule_id, path)
                    for rule_id in self.requested_rules
                )
            ]
            if results
            else []
        )
