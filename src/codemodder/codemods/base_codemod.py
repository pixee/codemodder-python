from dataclasses import dataclass
from enum import Enum
from typing import List, ClassVar

from libcst._position import CodeRange

from codemodder.change import Change
from codemodder.context import CodemodExecutionContext
from codemodder.file_context import FileContext


class ReviewGuidance(Enum):
    MERGE_AFTER_REVIEW = 1
    MERGE_AFTER_CURSORY_REVIEW = 2
    MERGE_WITHOUT_REVIEW = 3


@dataclass(frozen=True)
class CodemodMetadata:
    DESCRIPTION: str  # TODO: this field should be optional
    NAME: str
    REVIEW_GUIDANCE: ReviewGuidance


class BaseCodemod:
    # Implementation borrowed from https://stackoverflow.com/a/45250114
    METADATA: ClassVar[CodemodMetadata] = NotImplemented
    SUMMARY: ClassVar[str] = NotImplemented
    is_semgrep = False

    execution_context: CodemodExecutionContext
    file_context: FileContext

    def __init__(self, execution_context: CodemodExecutionContext, file_context):
        self.execution_context = execution_context
        self.file_context = file_context

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

    def add_change(self, node, description):
        position = self.node_position(node)
        self.add_change_from_position(position, description)

    def add_change_from_position(self, position: CodeRange, description):
        self.file_context.codemod_changes.append(
            Change(
                lineNumber=position.start.line,
                description=description,
            ).to_json()
        )

    def lineno_for_node(self, node):
        return self.node_position(node).start.line

    @property
    def line_exclude(self):
        return self.file_context.line_exclude

    @property
    def line_include(self):
        return self.file_context.line_include


class SemgrepCodemod(BaseCodemod):
    YAML_FILES: ClassVar[List[str]] = NotImplemented
    is_semgrep = True

    def __init__(self, *args):
        super().__init__(*args)
        self._results = (
            self.file_context.results_by_id.get(
                self.METADATA.NAME  # pylint: disable=no-member
            )
            or []
        )

    @property
    def should_transform(self):
        """Semgrep codemods should attempt transform only if there are
        semgrep results"""
        return bool(self._results)
