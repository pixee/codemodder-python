import logging
from pathlib import Path
import itertools
from textwrap import indent

from codemodder.change import ChangeSet
from codemodder.dependency import Dependency
from codemodder.dependency_manager import DependencyManager
from codemodder.executor import CodemodExecutorWrapper
from codemodder.logging import logger, log_list
from codemodder.registry import CodemodRegistry
from codemodder.project_analysis.python_repo_manager import PythonRepoManager


DEPENDENCY_NOTIFICATION = """```
💡 This codemod adds a dependency to your project. \
Currently we add the dependency to a file named `requirements.txt` if it \
exists in your project.

There are a number of other places where Python project dependencies can be \
expressed, including `setup.py`, `pyproject.toml`, and `setup.cfg`. We are \
working on adding support for these files, but for now you may need to update \
these files manually before accepting this change.
```
"""


class CodemodExecutionContext:  # pylint: disable=too-many-instance-attributes
    _results_by_codemod: dict[str, list[ChangeSet]] = {}
    _failures_by_codemod: dict[str, list[Path]] = {}
    dependencies: dict[str, set[Dependency]] = {}
    directory: Path
    dry_run: bool = False
    verbose: bool = False
    registry: CodemodRegistry
    repo_manager: PythonRepoManager

    def __init__(
        self,
        directory: Path,
        dry_run: bool,
        verbose: bool,
        registry: CodemodRegistry,
        repo_manager: PythonRepoManager,
    ):  # pylint: disable=too-many-arguments
        self.directory = directory
        self.dry_run = dry_run
        self.verbose = verbose
        self._results_by_codemod = {}
        self._failures_by_codemod = {}
        self.dependencies = {}
        self.registry = registry
        self.repo_manager = repo_manager

    def add_result(self, codemod_name, change_set):
        self._results_by_codemod.setdefault(codemod_name, []).append(change_set)

    def add_failure(self, codemod_name, file_path):
        self._failures_by_codemod.setdefault(codemod_name, []).append(file_path)

    def add_dependencies(self, codemod_id: str, dependencies: set[Dependency]):
        self.dependencies.setdefault(codemod_id, set()).update(dependencies)

    def get_results(self, codemod_name):
        return self._results_by_codemod.get(codemod_name, [])

    def get_changed_files(self):
        return [
            change_set.path
            for changes in self._results_by_codemod.values()
            for change_set in changes
        ]

    def get_failures(self, codemod_name):
        return self._failures_by_codemod.get(codemod_name, [])

    def get_failed_files(self):
        return list(
            itertools.chain.from_iterable(
                failures for failures in self._failures_by_codemod.values()
            )
        )

    def process_dependencies(self, codemod_id: str):
        dependencies = self.dependencies.get(codemod_id)
        if not dependencies:
            return

        dm = DependencyManager(self.directory)
        if not dm.found_dependency_file:
            logger.info(
                "unable to write dependencies for %s: no dependency file found",
                codemod_id,
            )
            return

        dm.add(list(dependencies))
        if (changeset := dm.write(self.dry_run)) is not None:
            self.add_result(codemod_id, changeset)

    def add_description(self, codemod: CodemodExecutorWrapper):
        description = codemod.description
        if codemod.adds_dependency:
            description = f"{description}\n\n{DEPENDENCY_NOTIFICATION}"

        return description

    def compile_results(self, codemods: list[CodemodExecutorWrapper]):
        results = []
        for codemod in codemods:
            data = {
                "codemod": codemod.id,
                "summary": codemod.summary,
                "description": self.add_description(codemod),
                "references": codemod.references,
                "properties": {},
                "failedFiles": [str(file) for file in self.get_failures(codemod.id)],
                "changeset": [
                    change.to_json() for change in self.get_results(codemod.id)
                ],
            }

            results.append(data)

        return results

    def log_changes(self, codemod_id: str):
        if failures := self.get_failures(codemod_id):
            log_list(logging.INFO, "failed", failures)
        if changes := self.get_results(codemod_id):
            logger.info("changed:")
            for change in changes:
                logger.info("  - %s", change.path)
                logger.debug("    diff:\n%s", indent(change.diff, " " * 6))
