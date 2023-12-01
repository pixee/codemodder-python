from importlib.abc import Traversable
from pathlib import Path

from wrapt import CallableObjectProxy


class CodemodExecutorWrapper(CallableObjectProxy):
    """A wrapper around a codemod that provides additional metadata."""

    origin: str
    docs_module: Traversable
    semgrep_config_module: Traversable

    def __init__(
        self,
        codemod,
        origin: str,
        docs_module: Traversable,
        semgrep_config_module: Traversable,
    ):
        super().__init__(codemod)
        self.origin = origin
        self.docs_module = docs_module
        self.semgrep_config_module = semgrep_config_module

    def apply(self, context, files: list[Path]):
        """
        Wraps the codemod's apply method to inject additional arguments.

        Not all codemods will need these arguments.
        """
        return self.apply_rule(
            context,
            yaml_files=self.yaml_files,
            files_to_analyze=files,
        )

    @property
    def name(self):
        return self.__wrapped__.name()

    @property
    def id(self):
        return f"{self.origin}:python/{self.name}"

    @property
    def is_semgrep(self):
        return self.__wrapped__.is_semgrep

    @property
    def summary(self):
        return self.SUMMARY

    def _get_description(self):
        doc_path = self.docs_module / f"{self.origin}_python_{self.name}.md"
        return doc_path.read_text()

    @property
    def description(self):
        try:
            return self._get_description()
        except FileNotFoundError:
            # TODO: temporary workaround
            return self.METADATA.DESCRIPTION

    @property
    def review_guidance(self):
        return self.METADATA.REVIEW_GUIDANCE.name.replace("_", " ").title()

    @property
    def references(self):
        return self.METADATA.REFERENCES

    @property
    def yaml_files(self):
        return [
            self.semgrep_config_module / yaml_file
            for yaml_file in getattr(self, "YAML_FILES", [])
        ]

    def describe(self):
        return {
            "codemod": self.id,
            "summary": self.summary,
            "description": self.description,
            "references": self.references,
        }

    def __repr__(self):
        return "<{} at 0x{:x} for {}.{}>".format(
            type(self).__name__,
            id(self),
            self.__wrapped__.__module__,
            self.__wrapped__.__name__,
        )

    # The following methods are all abstract in the ObjectProxy class, so
    # we just implement them as simple pass-throughs to the wrapped object.
    def __copy__(self):
        return self.__wrapped__.__copy__()

    def __deepcopy__(self, memo):
        return self.__wrapped__.__deepcopy__(memo)

    def __reduce__(self):
        return self.__wrapped__.__reduce__()

    def __reduce_ex__(self, protocol):
        return self.__wrapped__.__reduce_ex__(protocol)
