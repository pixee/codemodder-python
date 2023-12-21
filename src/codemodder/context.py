import logging
from pathlib import Path
import itertools
from textwrap import indent
from typing import List, Iterator

from codemodder.change import ChangeSet
from codemodder.dependency import (
    Dependency,
    build_dependency_notification,
    build_failed_dependency_notification,
)
from codemodder.executor import CodemodExecutorWrapper
from codemodder.file_context import FileContext
from codemodder.logging import logger, log_list
from codemodder.project_analysis.file_parsers.package_store import PackageStore
from codemodder.registry import CodemodRegistry
from codemodder.project_analysis.python_repo_manager import PythonRepoManager
from codemodder.utils.timer import Timer


class CodemodExecutionContext:  # pylint: disable=too-many-instance-attributes
    _results_by_codemod: dict[str, list[ChangeSet]] = {}
    _failures_by_codemod: dict[str, list[Path]] = {}
    _dependency_update_by_codemod: dict[str, PackageStore | None] = {}
    dependencies: dict[str, set[Dependency]] = {}
    directory: Path
    dry_run: bool = False
    verbose: bool = False
    registry: CodemodRegistry
    repo_manager: PythonRepoManager
    timer: Timer

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
        self.timer = Timer()

    def add_results(self, codemod_name: str, change_sets: List[ChangeSet]):
        self._results_by_codemod.setdefault(codemod_name, []).extend(change_sets)

    def add_failures(self, codemod_name: str, failed_files: List[Path]):
        self._failures_by_codemod.setdefault(codemod_name, []).extend(failed_files)

    def add_dependencies(self, codemod_id: str, dependencies: set[Dependency]):
        self.dependencies.setdefault(codemod_id, set()).update(dependencies)

    def get_results(self, codemod_name: str):
        return self._results_by_codemod.get(codemod_name, [])

    def get_changed_files(self):
        return [
            change_set.path
            for changes in self._results_by_codemod.values()
            for change_set in changes
        ]

    def get_failures(self, codemod_name: str):
        return self._failures_by_codemod.get(codemod_name, [])

    def get_failed_files(self):
        return list(
            itertools.chain.from_iterable(
                failures for failures in self._failures_by_codemod.values()
            )
        )

    def process_dependencies(
        self, codemod_id: str
    ) -> dict[Dependency, PackageStore | None]:
        """Write the dependencies a codemod added to the appropriate dependency
        file in the project. Returns a dict listing the locations the dependencies were added.
        """
        dependencies = self.dependencies.get(codemod_id)
        if not dependencies:
            return {}

        # populate everything with None and then change the ones added
        record: dict[Dependency, PackageStore | None] = {}
        for dep in dependencies:
            record[dep] = None

        store_list = self.repo_manager.package_stores
        if not store_list:
            logger.info(
                "unable to write dependencies for %s: no dependency file found",
                codemod_id,
            )
            self._dependency_update_by_codemod[codemod_id] = None
            return record

        # pylint: disable-next=cyclic-import
        from codemodder.dependency_management import DependencyManager

        for package_store in store_list:
            dm = DependencyManager(package_store, self.directory)
            if (changeset := dm.write(list(dependencies), self.dry_run)) is not None:
                self.add_results(codemod_id, [changeset])
                self._dependency_update_by_codemod[codemod_id] = package_store
                for dep in dependencies:
                    record[dep] = package_store
                break

        return record

    def add_description(self, codemod: CodemodExecutorWrapper):
        description = codemod.description
        if dependencies := list(self.dependencies.get(codemod.id, [])):
            if pkg_store := self._dependency_update_by_codemod.get(codemod.id):
                description += build_dependency_notification(
                    pkg_store.type.value, dependencies[0]
                )
            else:
                description += build_failed_dependency_notification(dependencies[0])

        return description

    def process_results(self, codemod_id: str, results: Iterator[FileContext]):
        for file_context in results:
            self.add_results(codemod_id, file_context.results)
            self.add_failures(codemod_id, file_context.failures)
            self.add_dependencies(codemod_id, file_context.dependencies)
            self.timer.aggregate(file_context.timer)

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
