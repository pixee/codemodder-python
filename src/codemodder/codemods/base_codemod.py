from dataclasses import dataclass, field
from enum import Enum
from typing import List, ClassVar

from libcst._position import CodeRange

from codemodder.change import Change
from codemodder.dependency import Dependency
from codemodder.file_context import FileContext
from codemodder.result import ResultSet
from codemodder.semgrep import run as semgrep_run


class ReviewGuidance(Enum):
    MERGE_AFTER_REVIEW = 1
    MERGE_AFTER_CURSORY_REVIEW = 2
    MERGE_WITHOUT_REVIEW = 3


@dataclass(frozen=True)
class CodemodMetadata:
    DESCRIPTION: str  # TODO: this field should be optional
    NAME: str
    REVIEW_GUIDANCE: ReviewGuidance
    REFERENCES: list = field(default_factory=list)

    # TODO: remove post_init update_references once we add description for each url.
    def __post_init__(self):
        object.__setattr__(self, "REFERENCES", self.update_references(self.REFERENCES))

    @staticmethod
    def update_references(references):
        updated_references = []
        for reference in references:
            updated_reference = dict(
                reference
            )  # Create a copy to avoid modifying the original dict
            updated_reference["description"] = updated_reference["url"]
            updated_references.append(updated_reference)
        return updated_references


class BaseCodemod:
    # Implementation borrowed from https://stackoverflow.com/a/45250114
    METADATA: ClassVar[CodemodMetadata] = NotImplemented
    SUMMARY: ClassVar[str] = NotImplemented
    is_semgrep: bool = False
    adds_dependency: bool = False
    file_context: FileContext

    def __init__(self, file_context: FileContext):
        self.file_context = file_context

    @classmethod
    def apply_rule(cls, context, *args, **kwargs) -> ResultSet:
        """
        Apply rule associated with this codemod and gather results

        Does nothing by default. Subclasses may override for custom rule logic.
        """
        del context, args, kwargs
        return ResultSet()

    @classmethod
    def name(cls):
        # pylint: disable=no-member
        return cls.METADATA.NAME

    @property
    def should_transform(self):
        return True

    def node_position(self, node):
        # pylint: disable=no-member
        # See https://github.com/Instagram/LibCST/blob/main/libcst/_metadata_dependent.py#L112
        return self.get_metadata(self.METADATA_DEPENDENCIES[0], node)

    def add_change(self, node, description: str, start: bool = True):
        position = self.node_position(node)
        self.add_change_from_position(position, description, start)

    def add_change_from_position(
        self, position: CodeRange, description: str, start: bool = True
    ):
        lineno = position.start.line if start else position.end.line
        self.file_context.codemod_changes.append(
            Change(
                lineNumber=lineno,
                description=description,
            )
        )

    def lineno_for_node(self, node):
        return self.node_position(node).start.line

    @property
    def line_exclude(self):
        return self.file_context.line_exclude

    @property
    def line_include(self):
        return self.file_context.line_include

    def add_dependency(self, dependency: Dependency):
        self.file_context.add_dependency(dependency)


class SemgrepCodemod(BaseCodemod):
    YAML_FILES: ClassVar[List[str]] = NotImplemented
    is_semgrep = True

    @classmethod
    def apply_rule(cls, context, *args, **kwargs) -> ResultSet:
        """
        Apply semgrep to gather rule results
        """
        yaml_files = kwargs.get("yaml_files") or args[0]
        files_to_analyze = kwargs.get("files_to_analyze") or args[1]
        with context.timer.measure("semgrep"):
            return semgrep_run(context, yaml_files, files_to_analyze)

    @property
    def should_transform(self):
        """Semgrep codemods should attempt transform only if there are semgrep results"""
        return bool(self.file_context.findings)
