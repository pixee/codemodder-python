import argparse
import logging
from pathlib import Path
import itertools
from textwrap import indent

from codemodder.change import ChangeSet
from codemodder.dependency_manager import DependencyManager
from codemodder.executor import CodemodExecutorWrapper
from codemodder.logging import logger, log_list
from codemodder.registry import CodemodRegistry


class CodemodExecutionContext:  # pylint: disable=too-many-instance-attributes
    _results_by_codemod: dict[str, list[ChangeSet]] = {}
    _failures_by_codemod: dict[str, list[Path]] = {}
    dependencies: dict[str, set[str]] = {}
    directory: Path
    dry_run: bool = False
    verbose: bool = False
    registry: CodemodRegistry

    def __init__(
        self,
        cli_args: argparse.Namespace,
        registry: CodemodRegistry,
    ):
        self.directory = Path(cli_args.directory)
        self.dry_run = cli_args.dry_run
        self.verbose = cli_args.verbose
        self.path_include = cli_args.path_include
        self.path_exclude = cli_args.path_exclude
        self._results_by_codemod = {}
        self._failures_by_codemod = {}
        self.dependencies = {}
        self.registry = registry

    def add_result(self, codemod_name, change_set):
        self._results_by_codemod.setdefault(codemod_name, []).append(change_set)

    def add_failure(self, codemod_name, file_path):
        self._failures_by_codemod.setdefault(codemod_name, []).append(file_path)

    def add_dependencies(self, codemod_id: str, dependencies: set[str]):
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

    def compile_results(self, codemods: list[CodemodExecutorWrapper]):
        results = []
        for codemod in codemods:
            data = {
                "codemod": codemod.id,
                "summary": codemod.summary,
                "description": codemod.description,
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
