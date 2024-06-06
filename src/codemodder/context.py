from __future__ import annotations

import itertools
import logging
from pathlib import Path
from textwrap import indent
from typing import TYPE_CHECKING, Iterator, List

from codemodder.codetf import ChangeSet
from codemodder.codetf import Result as CodeTFResult
from codemodder.codetf import UnfixedFinding
from codemodder.dependency import (
    Dependency,
    build_dependency_notification,
    build_failed_dependency_notification,
)
from codemodder.file_context import FileContext
from codemodder.llm import setup_llm_client
from codemodder.logging import log_list, logger
from codemodder.project_analysis.file_parsers.package_store import PackageStore
from codemodder.project_analysis.python_repo_manager import PythonRepoManager
from codemodder.providers import ProviderRegistry
from codemodder.registry import CodemodRegistry
from codemodder.utils.timer import Timer

if TYPE_CHECKING:
    from openai import OpenAI

    from codemodder.codemods.base_codemod import BaseCodemod


class CodemodExecutionContext:
    _failures_by_codemod: dict[str, list[Path]] = {}
    _dependency_update_by_codemod: dict[str, PackageStore | None] = {}
    _unfixed_findings_by_codemod: dict[str, list[UnfixedFinding]] = {}
    dependencies: dict[str, set[Dependency]] = {}
    directory: Path
    dry_run: bool = False
    verbose: bool = False
    registry: CodemodRegistry
    providers: ProviderRegistry
    repo_manager: PythonRepoManager
    timer: Timer
    path_include: list[str]
    path_exclude: list[str]
    max_workers: int = 1
    tool_result_files_map: dict[str, list[str]]
    llm_client: OpenAI | None = None

    def __init__(
        self,
        directory: Path,
        dry_run: bool,
        verbose: bool,
        registry: CodemodRegistry,
        providers: ProviderRegistry,
        repo_manager: PythonRepoManager,
        path_include: list[str],
        path_exclude: list[str],
        tool_result_files_map: dict[str, list[str]] | None = None,
        max_workers: int = 1,
    ):
        self.directory = directory
        self.dry_run = dry_run
        self.verbose = verbose
        self._changesets_by_codemod: dict[str, list[ChangeSet]] = {}
        self._failures_by_codemod = {}
        self._dependency_update_by_codemod = {}
        self._unfixed_findings_by_codemod = {}
        self.dependencies = {}
        self.registry = registry
        self.providers = providers
        self.repo_manager = repo_manager
        self.timer = Timer()
        self.path_include = path_include
        self.path_exclude = path_exclude
        self.max_workers = max_workers
        self.tool_result_files_map = tool_result_files_map or {}
        self.llm_client = setup_llm_client()

    def add_changesets(self, codemod_name: str, change_sets: List[ChangeSet]):
        self._changesets_by_codemod.setdefault(codemod_name, []).extend(change_sets)

    def add_failures(self, codemod_name: str, failed_files: List[Path]):
        self._failures_by_codemod.setdefault(codemod_name, []).extend(failed_files)

    def add_dependencies(self, codemod_id: str, dependencies: set[Dependency]):
        self.dependencies.setdefault(codemod_id, set()).update(dependencies)

    def get_changesets(self, codemod_name: str) -> list[ChangeSet]:
        return self._changesets_by_codemod.get(codemod_name, [])

    def get_changed_files(self):
        return [
            change_set.path
            for changes in self._changesets_by_codemod.values()
            for change_set in changes
        ]

    def get_failures(self, codemod_name: str) -> list[Path]:
        return self._failures_by_codemod.get(codemod_name, [])

    def get_failed_files(self) -> list[Path]:
        return list(
            itertools.chain.from_iterable(
                failures for failures in self._failures_by_codemod.values()
            )
        )

    def get_unfixed_findings(self, codemod_name: str) -> list[UnfixedFinding]:
        return self._unfixed_findings_by_codemod.get(codemod_name, [])

    def process_dependencies(
        self, codemod_id: str
    ) -> dict[Dependency, PackageStore | None]:
        """Write the dependencies a codemod added to the appropriate dependency
        file in the project. Returns a dict listing the locations the dependencies were added.
        """
        if not (dependencies := self.dependencies.get(codemod_id)):
            return {}

        # populate everything with None and then change the ones added
        record: dict[Dependency, PackageStore | None] = {}
        for dep in dependencies:
            record[dep] = None

        if not (store_list := self.repo_manager.package_stores):
            logger.info(
                "unable to write dependencies for %s: no dependency file found",
                codemod_id,
            )
            self._dependency_update_by_codemod[codemod_id] = None
            return record

        from codemodder.dependency_management import DependencyManager

        for package_store in store_list:
            dm = DependencyManager(package_store, self.directory)
            if (changeset := dm.write(list(dependencies), self.dry_run)) is not None:
                self.add_changesets(codemod_id, [changeset])
                self._dependency_update_by_codemod[codemod_id] = package_store
                for dep in dependencies:
                    record[dep] = package_store
                break

        return record

    def add_description(self, codemod: BaseCodemod):
        description = codemod.description
        if dependencies := list(self.dependencies.get(codemod.id, [])):
            if pkg_store := self._dependency_update_by_codemod.get(codemod.id):
                description += build_dependency_notification(
                    pkg_store.type.value, dependencies[0]
                )
            else:
                description += build_failed_dependency_notification(dependencies[0])

        return description

    def add_unfixed_findings(
        self, codemod_id: str, unfixed_findings: list[UnfixedFinding]
    ):
        self._unfixed_findings_by_codemod.setdefault(codemod_id, []).extend(
            unfixed_findings
        )

    def process_results(self, codemod_id: str, results: Iterator[FileContext]):
        for file_context in results:
            self.add_changesets(codemod_id, file_context.changesets)
            self.add_failures(codemod_id, file_context.failures)
            self.add_dependencies(codemod_id, file_context.dependencies)
            self.add_unfixed_findings(codemod_id, file_context.unfixed_findings)
            self.timer.aggregate(file_context.timer)

    def compile_results(self, codemods: list[BaseCodemod]) -> list[CodeTFResult]:
        results = []
        for codemod in codemods:
            result = CodeTFResult(
                codemod=codemod.id,
                summary=codemod.summary,
                description=self.add_description(codemod),
                detectionTool=codemod.detection_tool,
                references=codemod.references,
                properties={},
                failedFiles=[str(file) for file in self.get_failures(codemod.id)],
                changeset=self.get_changesets(codemod.id),
                unfixedFindings=self.get_unfixed_findings(codemod.id),
            )

            results.append(result)

        return results

    def log_changes(self, codemod_id: str):
        if failures := self.get_failures(codemod_id):
            log_list(logging.INFO, "failed", failures)
        if changes := self.get_changesets(codemod_id):
            logger.info("changed:")
            for change in changes:
                logger.info("  - %s", change.path)
                logger.debug("    diff:\n%s", indent(change.diff, " " * 6))
