from dataclasses import dataclass, asdict
from importlib.abc import Traversable
from importlib.resources import files
from importlib.metadata import entry_points
from typing import Optional

from codemodder.logging import logger


@dataclass
class CodemodCollection:
    """A collection of codemods that all share the same origin and documentation."""

    origin: str
    docs_module: str
    semgrep_config_module: str
    codemods: list


@dataclass
class _CodemodWrapper:
    """A wrapper around a codemod that provides additional metadata."""

    origin: str
    codemod: type
    docs_module: Traversable
    semgrep_config_module: Traversable

    def __call__(self, *args, **kwargs):
        return self.codemod(*args, **kwargs)

    @property
    def name(self):
        return self.codemod.name()

    @property
    def id(self):
        return f"{self.origin}:python/{self.name}"

    @property
    def YAML_FILES(self):
        return self.codemod.YAML_FILES

    @property
    def is_semgrep(self):
        return self.codemod.is_semgrep

    @property
    def summary(self):
        return self.codemod.SUMMARY

    def _get_description(self):
        doc_path = self.docs_module / f"{self.origin}_python_{self.name}.md"
        return doc_path.read_text()

    @property
    def description(self):
        try:
            return self._get_description()
        except FileNotFoundError:
            # TODO: temporary workaround
            return self.codemod.METADATA.DESCRIPTION

    @property
    def yaml_files(self):
        return [self.semgrep_config_module / yaml_file for yaml_file in self.YAML_FILES]


class CodemodRegistry:
    _codemods: list[_CodemodWrapper]

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
        return [codemod.codemod for codemod in self._codemods]

    def add_codemod_collection(self, collection: CodemodCollection):
        docs_module = files(collection.docs_module)
        semgrep_module = files(collection.semgrep_config_module)
        for codemod in collection.codemods:
            self._validate_codemod(codemod)
            self._codemods.append(
                _CodemodWrapper(
                    collection.origin,
                    codemod,
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
