import itertools
from typing import List, ClassVar


class BaseCodemod:
    # Implementation borrowed from https://stackoverflow.com/a/45250114
    NAME: ClassVar[str] = NotImplemented
    DESCRIPTION: ClassVar[str] = NotImplemented
    RULE_IDS: List[str] = NotImplemented
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
        if cls.RULE_IDS is NotImplemented:
            raise NotImplementedError("You forgot to define class attribute: RULE_IDS")

    def __init__(self, results_by_id):
        self._results = list(
            itertools.chain.from_iterable(
                map(lambda rId: results_by_id[rId], self.RULE_IDS)
            )
        )

    @classmethod
    def full_name(cls):
        return f"pixee:python/{cls.NAME}"
