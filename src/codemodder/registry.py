from dataclasses import dataclass, asdict
from importlib.resources import files
from importlib.metadata import entry_points
from typing import Optional

from codemodder.executor import CodemodExecutorWrapper
from codemodder.logging import logger


@dataclass
class CodemodCollection:
    """A collection of codemods that all share the same origin and documentation."""

    origin: str
    docs_module: str
    semgrep_config_module: str
    codemods: list


class CodemodRegistry:
    _codemods: list[CodemodExecutorWrapper]

    def __init__(self):
        self._codemods = []

    @property
    def names(self):
        return [codemod.name for codemod in self._codemods]

    @property
    def ids(self):
        return [codemod.id for codemod in self._codemods]

    @property
    def codemods(self):
        return self._codemods

    def add_codemod_collection(self, collection: CodemodCollection):
        docs_module = files(collection.docs_module)
        semgrep_module = files(collection.semgrep_config_module)
        for codemod in collection.codemods:
            self._validate_codemod(codemod)
            self._codemods.append(
                CodemodExecutorWrapper(
                    codemod,
                    collection.origin,
                    docs_module,
                    semgrep_module,
                )
            )

    def _validate_codemod(self, codemod):
        for name in ["SUMMARY", "METADATA"]:
            if not (attr := getattr(codemod, name)) or attr is NotImplemented:
                raise ValueError(
                    f'Missing required attribute "{name}" on codemod {codemod}'
                )

        for k, v in asdict(codemod.METADATA).items():
            if v is NotImplemented:
                raise NotImplementedError(f"METADATA.{k} not defined for {codemod}")
            if not v:
                raise NotImplementedError(
                    f"METADATA.{k} should not be None or empty for {codemod}"
                )

        # TODO: eventually we will represent IS_SEMGREP using the class hierarchy
        if codemod.is_semgrep and not codemod.YAML_FILES:
            raise ValueError(
                f"Missing required attribute YAML_FILES on semgrep codemod {codemod}"
            )

    def match_codemods(
        self,
        codemod_include: Optional[list] = None,
        codemod_exclude: Optional[list] = None,
    ) -> dict:
        if not codemod_include and not codemod_exclude:
            return {codemod.name: codemod for codemod in self._codemods}

        codemod_include = codemod_include or []
        codemod_exclude = codemod_exclude or []

        # cli should've already prevented both include/exclude from being set.
        assert codemod_include or codemod_exclude

        # TODO: preserve order of includes
        if codemod_exclude:
            return {
                name: codemod
                for codemod in self._codemods
                if (name := codemod.name) not in codemod_exclude
                and codemod.id not in codemod_exclude
            }

        return {
            name: codemod
            for codemod in self._codemods
            if (name := codemod.name) in codemod_include
            or codemod.id in codemod_include
        }


def load_registered_codemods() -> CodemodRegistry:
    registry = CodemodRegistry()
    logger.info("Loading registered codemod collections")
    for entry_point in entry_points()["codemods"]:
        logger.debug(
            'Loading codemod collection "%s" from "%s"',
            entry_point.name,
            entry_point.module,
        )
        collection = entry_point.load()
        registry.add_codemod_collection(collection)
    return registry
