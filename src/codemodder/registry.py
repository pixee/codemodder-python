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
    _codemods_by_name: dict[str, CodemodExecutorWrapper]
    _codemods_by_id: dict[str, CodemodExecutorWrapper]

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
        docs_module = files(collection.docs_module)
        semgrep_module = files(collection.semgrep_config_module)
        for codemod in collection.codemods:
            self._validate_codemod(codemod)
            wrapper = CodemodExecutorWrapper(
                codemod,
                collection.origin,
                docs_module,
                semgrep_module,
            )
            self._codemods_by_name[wrapper.name] = wrapper
            self._codemods_by_id[wrapper.id] = wrapper

    def _validate_codemod(self, codemod):
        for name in ["SUMMARY", "METADATA"]:
            if not (attr := getattr(codemod, name)) or attr is NotImplemented:
                raise ValueError(
                    f'Missing required attribute "{name}" on codemod {codemod}'
                )

        for k, v in asdict(codemod.METADATA).items():
            if v is NotImplemented:
                raise NotImplementedError(f"METADATA.{k} not defined for {codemod}")
            if k != "REFERENCES" and not v:
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
    ) -> list[CodemodExecutorWrapper]:
        if not codemod_include and not codemod_exclude:
            return self.codemods

        codemod_include = codemod_include or []
        codemod_exclude = codemod_exclude or []

        # cli should've already prevented both include/exclude from being set.
        assert codemod_include or codemod_exclude

        if codemod_exclude:
            return [
                codemod
                for codemod in self.codemods
                if codemod.name not in codemod_exclude
                and codemod.id not in codemod_exclude
            ]

        return [
            self._codemods_by_name.get(name) or self._codemods_by_id[name]
            for name in codemod_include
        ]


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
