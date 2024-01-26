from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import entry_points
from typing import Optional, TYPE_CHECKING

from codemodder.logging import logger

if TYPE_CHECKING:
    from codemodder.codemods.base_codemod import BaseCodemod


# These are generally not intended to be applied directly so they are excluded by default.
DEFAULT_EXCLUDED_CODEMODS = [
    "pixee:python/order-imports",
    "pixee:python/unused-imports",
    # See https://github.com/pixee/codemodder-python/pull/212 for concerns regarding this codemod.
    "pixee:python/fix-empty-sequence-comparison",
]


@dataclass
class CodemodCollection:
    """A collection of codemods that all share the same origin and documentation."""

    origin: str
    docs_module: str
    semgrep_config_module: str
    codemods: list


class CodemodRegistry:
    _codemods_by_name: dict[str, BaseCodemod]
    _codemods_by_id: dict[str, BaseCodemod]

    def __init__(self):
        self._codemods_by_name = {}
        self._codemods_by_id = {}

    @property
    def names(self):
        return list(self._codemods_by_name.keys())

    @property
    def ids(self):
        return list(self._codemods_by_id.keys())

    @property
    def codemods(self):
        return list(self._codemods_by_name.values())

    def add_codemod_collection(self, collection: CodemodCollection):
        for codemod in collection.codemods:
            wrapper = codemod() if isinstance(codemod, type) else codemod
            self._codemods_by_name[wrapper.name] = wrapper
            self._codemods_by_id[wrapper.id] = wrapper

    def match_codemods(
        self,
        codemod_include: Optional[list] = None,
        codemod_exclude: Optional[list] = None,
        sast_only=False,
    ) -> list[BaseCodemod]:
        codemod_include = codemod_include or []
        codemod_exclude = codemod_exclude or DEFAULT_EXCLUDED_CODEMODS
        base_list = [
            codemod
            for codemod in self.codemods
            if (sast_only and codemod.origin != "pixee")
            or (not sast_only and codemod.origin == "pixee")
        ]

        if codemod_exclude and not codemod_include:
            return [
                codemod
                for codemod in base_list
                if codemod.name not in codemod_exclude
                and codemod.id not in codemod_exclude
            ]

        return [
            self._codemods_by_name.get(name) or self._codemods_by_id[name]
            for name in codemod_include
        ]

    def describe_codemods(
        self,
        codemod_include: Optional[list] = None,
        codemod_exclude: Optional[list] = None,
    ) -> list[dict]:
        codemods = self.match_codemods(codemod_include, codemod_exclude)
        return [codemod.describe() for codemod in codemods]


def load_registered_codemods() -> CodemodRegistry:
    registry = CodemodRegistry()
    logger.debug("loading registered codemod collections")
    for entry_point in entry_points().select(group="codemods"):
        logger.debug(
            '- loading codemod collection "%s" from "%s"',
            entry_point.name,
            entry_point.module,
        )
        collection = entry_point.load()
        registry.add_codemod_collection(collection)
    return registry
