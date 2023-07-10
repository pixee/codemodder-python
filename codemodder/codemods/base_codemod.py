import itertools
from typing import List, ClassVar
from codemodder.semgrep import rule_ids_from_yaml_files


class BaseCodemod:
    # Implementation borrowed from https://stackoverflow.com/a/45250114
    NAME: ClassVar[str] = NotImplemented
    DESCRIPTION: ClassVar[str] = NotImplemented
    YAML_FILES: List[str] = NotImplemented
    CHANGESET_ALL_FILES: List = []
    CHANGES_IN_FILE: List = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Generalize this
        if cls.NAME is NotImplemented:
            raise NotImplementedError("You forgot to define class attribute: NAME")
        if cls.DESCRIPTION is NotImplemented:
            raise NotImplementedError(
                "You forgot to define class attribute: DESCRIPTION"
            )
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
        return f"pixee:python/{cls.NAME}"
