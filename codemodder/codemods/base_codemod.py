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
    DESCRIPTION: str
    NAME: str
    REVIEW_GUIDANCE: ReviewGuidance


class BaseCodemod:
    # Implementation borrowed from https://stackoverflow.com/a/45250114
    METADATA: ClassVar[CodemodMetadata] = NotImplemented
    CHANGESET_ALL_FILES: ClassVar[List] = []
    CHANGES_IN_FILE: ClassVar[List] = []
    RULE_IDS: ClassVar[List] = []
    YAML_FILES: ClassVar[List[str]] = NotImplemented

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Generalize this
        if cls.METADATA is NotImplemented:
            raise NotImplementedError("You forgot to define METADATA")
        for k, v in asdict(cls.METADATA).items():
            if v is NotImplemented:
                raise NotImplementedError(f"You forgot to define METADATA.{k}")
            if not v:
                raise NotImplementedError(f"METADATA.{k} should not be None or empty")
        if cls.YAML_FILES is NotImplemented:
            raise NotImplementedError(
                "You forgot to define class attribute: YAML_FILES"
            )

        cls.RULE_IDS = rule_ids_from_yaml_files(cls.YAML_FILES)

    def __init__(self, file_context):
        self.file_context = file_context
        self._results = list(
            itertools.chain.from_iterable(
                map(lambda rId: file_context.results_by_id[rId], self.RULE_IDS)
            )
        )

    @classmethod
    def full_name(cls):
        # pylint: disable=no-member
        return f"pixee:python/{cls.METADATA.NAME}"

    @property
    def should_transform(self):
        # Determine if a codemod should attempt a tranformation based on
        # if semgrep results exist.
        return bool(self._results)
