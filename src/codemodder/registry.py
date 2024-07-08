from __future__ import annotations

import os
import re
from dataclasses import dataclass
from importlib.metadata import EntryPoint, entry_points
from itertools import chain
from typing import TYPE_CHECKING, Callable, Optional

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
    _codemods_by_id: dict[str, BaseCodemod]
    _default_include_paths: set[str]

    def __init__(self):
        self._codemods_by_id = {}
        self._default_include_paths = set()

    @property
    def ids(self):
        return list(self._codemods_by_id.keys())

    @property
    def codemods(self):
        return list(self._codemods_by_id.values())

    @property
    def default_include_paths(self) -> list[str]:
        return list(self._default_include_paths)

    def add_codemod_collection(self, collection: CodemodCollection):
        for codemod in collection.codemods:
            wrapper = codemod() if isinstance(codemod, type) else codemod
            self._codemods_by_id[wrapper.id] = wrapper
            self._default_include_paths.update(
                chain(
                    *[
                        (f"*{ext}", os.path.join("**", f"*{ext}"))
                        for ext in wrapper.default_extensions
                    ]
                )
            )

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
            patterns = [
                re.compile(exclude.replace("*", ".*"))
                for exclude in codemod_exclude
                if "*" in exclude
            ]
            names = set(name for name in codemod_exclude if "*" not in name)

            for codemod in self.codemods:
                if codemod.id in names or any(
                    pat.match(codemod.id) for pat in patterns
                ):
                    continue

                if bool(sast_only) != bool(codemod.origin == "pixee"):
                    base_codemods[codemod.id] = codemod

            # Remove duplicates and preserve order
            return list(base_codemods.values())

        matched_codemods = []
        for name in codemod_include:
            if "*" in name:
                pat = re.compile(name.replace("*", ".*"))
                pattern_matches = [code for code in self.codemods if pat.match(code.id)]
                matched_codemods.extend(pattern_matches)
                if not pattern_matches:
                    logger.warning(
                        "Given codemod pattern '%s' does not match any codemods.", name
                    )
                continue

            try:
                matched_codemods.append(self._codemods_by_id[name])
            except KeyError:
                logger.warning(f"Requested codemod to include '{name}' does not exist.")
        return matched_codemods

    def describe_codemods(
        self,
        codemod_include: Optional[list] = None,
        codemod_exclude: Optional[list] = None,
    ) -> list[dict]:
        codemods = self.match_codemods(codemod_include, codemod_exclude)
        return [codemod.describe() for codemod in codemods]


def load_registered_codemods(ep_filter: Optional[Callable[[EntryPoint], bool]] = None):
    registry = CodemodRegistry()
    logger.debug("loading registered codemod collections")
    for entry_point in entry_points().select(group="codemods"):
        if ep_filter and not ep_filter(entry_point):
            logger.debug(
                '- skipping codemod collection "%s" from "%s as requested"',
                entry_point.name,
                entry_point.module,
            )
            continue

        logger.debug(
            '- loading codemod collection "%s" from "%s"',
            entry_point.name,
            entry_point.module,
        )
        collection = entry_point.load()
        registry.add_codemod_collection(collection)
    return registry
