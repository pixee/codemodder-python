from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import entry_points
from typing import TYPE_CHECKING, Optional

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

        if codemod_exclude and not codemod_include:
            base_codemods = {}
            for codemod in self.codemods:
                if (sast_only and codemod.origin != "pixee") or (
                    not sast_only and codemod.origin == "pixee"
                ):
                    base_codemods[codemod.id] = codemod
                    base_codemods[codemod.name] = codemod

            for name_or_id in codemod_exclude:
                try:
                    codemod = base_codemods[name_or_id]
                except KeyError:
                    logger.warning(
                        f"Requested codemod to exclude'{name_or_id}' does not exist."
                    )
                    continue

                # remove both by name and id since we don't know which `name_or_id` represented
                base_codemods.pop(codemod.name, None)
                base_codemods.pop(codemod.id, None)
            # Remove duplicates and preserve order
            return list(dict.fromkeys(base_codemods.values()))

        matched_codemods = []
        for name in codemod_include:
            try:
                matched_codemods.append(
                    self._codemods_by_name.get(name) or self._codemods_by_id[name]
                )
            except KeyError:
                logger.warning(f"Requested codemod to include'{name}' does not exist.")
        return matched_codemods

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
