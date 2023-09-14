from dataclasses import dataclass, asdict
from enum import Enum
import itertools
from typing import List, ClassVar

from codemodder.context import CodemodExecutionContext
from codemodder.file_context import FileContext
from codemodder.semgrep import rule_ids_from_yaml_files


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
    IS_SEMGREP = False

    execution_context: CodemodExecutionContext
    file_context: FileContext

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if "codemodder.codemods.base_codemod.SemgrepCodemod" in str(cls):
            # hack: SemgrepCodemod won't NotImplementedError but all other child
            # classes will.
            return

        for attr in ["SUMMARY", "METADATA"]:
            if getattr(cls, attr) is NotImplemented:
                raise NotImplementedError(
                    f"You forgot to define {attr} for {cls.__name__}"
                )
        for k, v in asdict(cls.METADATA).items():
            if v is NotImplemented:
                raise NotImplementedError(f"You forgot to define METADATA.{k}")
            if not v:
                raise NotImplementedError(f"METADATA.{k} should not be None or empty")

    def __init__(self, execution_context: CodemodExecutionContext, file_context):
        self.execution_context = execution_context
        self.file_context = file_context

    @classmethod
    def name(cls):
        # pylint: disable=no-member
        return cls.METADATA.NAME

    @classmethod
    def id(cls):
        # pylint: disable=no-member
        return f"pixee:python/{cls.name()}"

    @property
    def should_transform(self):
        return True

    def node_position(self, node):
        # pylint: disable=no-member
        # See https://github.com/Instagram/LibCST/blob/main/libcst/_metadata_dependent.py#L112
        return self.get_metadata(self.METADATA_DEPENDENCIES[0], node)

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
    IS_SEMGREP = True

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if cls.YAML_FILES is NotImplemented:
            raise NotImplementedError(
                "You forgot to define class attribute: YAML_FILES"
            )

        cls.RULE_IDS = rule_ids_from_yaml_files(cls.YAML_FILES)

    def __init__(self, *args):
        super().__init__(*args)
        self._results = list(
            itertools.chain.from_iterable(
                map(lambda rId: self.file_context.results_by_id[rId], self.RULE_IDS)
            )
        )

    @property
    def should_transform(self):
        """Semgrep codemods should attempt transform only if there are
        semgrep results"""
        return bool(self._results)
