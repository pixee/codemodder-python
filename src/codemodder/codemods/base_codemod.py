from dataclasses import dataclass, asdict
from enum import Enum
import itertools
from typing import List, ClassVar
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
    IS_SEMGREP = False

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.CHANGESET_ALL_FILES: list = []

        if "codemodder.codemods.base_codemod.SemgrepCodemod" in str(cls):
            # hack: SemgrepCodemod won't NotImplementedError but all other child
            # classes will.
            return

        if cls.METADATA is NotImplemented:
            raise NotImplementedError("You forgot to define METADATA")
        for k, v in asdict(cls.METADATA).items():
            if v is NotImplemented:
                raise NotImplementedError(f"You forgot to define METADATA.{k}")
            if not v:
                raise NotImplementedError(f"METADATA.{k} should not be None or empty")

    def __init__(self, file_context):
        self.file_context = file_context

    @classmethod
    def full_name(cls):
        # pylint: disable=no-member
        return f"pixee:python/{cls.METADATA.NAME}"

    @property
    def should_transform(self):
        return True

    def node_position(self, node):
        # pylint: disable=no-member
        # See https://github.com/Instagram/LibCST/blob/main/libcst/_metadata_dependent.py#L112
        return self.get_metadata(self.METADATA_DEPENDENCIES[0], node)

    def lineno_for_node(self, node):
        return self.node_position(node).start.line


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

    def __init__(self, file_context):
        super().__init__(file_context)
        self._results = list(
            itertools.chain.from_iterable(
                map(lambda rId: file_context.results_by_id[rId], self.RULE_IDS)
            )
        )

    @property
    def should_transform(self):
        """Semgrep codemods should attempt transform only if there are
        semgrep results"""
        return bool(self._results)
