import datetime
import itertools
import logging
import os
import sys
from typing import Sequence
from pathlib import Path

from codemodder.dependency import Dependency

from codemodder import registry, __version__
from codemodder.logging import configure_logger, logger, log_section, log_list
from codemodder.cli import parse_args
from codemodder.code_directory import match_files
from codemodder.codemods.semgrep import SemgrepRuleDetector
from codemodder.context import CodemodExecutionContext
from codemodder.codemods.api import BaseCodemod
from codemodder.project_analysis.file_parsers.package_store import PackageStore
from codemodder.project_analysis.python_repo_manager import PythonRepoManager
from codemodder.report.codetf_reporter import report_default
from codemodder.result import ResultSet
from codemodder.semgrep import run as run_semgrep


def update_code(file_path, new_code):
    """
    Write the `new_code` to the `file_path`
    """
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_code)


def find_semgrep_results(
    context: CodemodExecutionContext,
    codemods: Sequence[BaseCodemod],
    files_to_analyze: list[Path] | None = None,
) -> ResultSet:
    """Run semgrep once with all configuration files from all codemods and return a set of applicable rule IDs"""
    yaml_files = list(
        itertools.chain.from_iterable(
            [
                codemod.detector.get_yaml_files(codemod.name)
                for codemod in codemods
                if codemod.detector
                and isinstance(codemod.detector, SemgrepRuleDetector)
            ]
        )
    )
    if not yaml_files:
        return ResultSet()

    return run_semgrep(context, yaml_files, files_to_analyze)


def log_report(context, argv, elapsed_ms, files_to_analyze):
    log_section("report")
    logger.info("scanned: %s files", len(files_to_analyze))
    all_failures = context.get_failed_files()
    logger.info(
        "failed: %s files (%s unique)",
        len(all_failures),
        len(set(all_failures)),
    )
    all_changes = context.get_changed_files()
    logger.info(
        "changed: %s files (%s unique)",
        len(all_changes),
        len(set(all_changes)),
    )
    logger.info("report file: %s", argv.output)
    logger.info("total elapsed: %s ms", elapsed_ms)
    logger.info("  semgrep:     %s ms", context.timer.get_time_ms("semgrep"))
    logger.info("  parse:       %s ms", context.timer.get_time_ms("parse"))
    logger.info("  transform:   %s ms", context.timer.get_time_ms("transform"))
    logger.info("  write:       %s ms", context.timer.get_time_ms("write"))


def apply_codemods(
    context: CodemodExecutionContext,
    codemods_to_run: Sequence[BaseCodemod],
    semgrep_results: ResultSet,
    files_to_analyze: list[Path],
):
    log_section("scanning")

    if not files_to_analyze:
        logger.info("no files to scan")
        return

    if not codemods_to_run:
        logger.info("no codemods to run")
        return

    semgrep_finding_ids = semgrep_results.all_rule_ids()

    # run codemods one at a time making sure to respect the given sequence
    for codemod in codemods_to_run:
        # NOTE: this may be used as a progress indicator by upstream tools
        logger.info("running codemod %s", codemod.id)

        if isinstance(codemod.detector, SemgrepRuleDetector):
            # Unfortunately the IDs from semgrep are not fully specified
            # TODO: eventually we need to be able to use fully specified IDs here
            if codemod.name not in semgrep_finding_ids:
                logger.debug(
                    "no results from semgrep for %s, skipping analysis",
                    codemod.id,
                )
                continue

            files_to_analyze = semgrep_results.files_for_rule(codemod.name)

        # Non-semgrep codemods ignore the semgrep results
        codemod.apply(context, files_to_analyze)
        record_dependency_update(context.process_dependencies(codemod.id))
        context.log_changes(codemod.id)


def record_dependency_update(dependency_results: dict[Dependency, PackageStore | None]):
    # TODO populate dependencies in CodeTF here
    inverse: dict[None | str, list[Dependency]] = {}
    for k, v in dependency_results.items():
        inv_key = str(v.file) if v else None
        if inv_key in inverse:
            inverse.get(inv_key, []).append(k)
        else:
            inverse[inv_key] = [k]

    for file in inverse.keys():
        str_list = str([d.requirement.name for d in inverse[file]])[2:-2]
        if file:
            logger.debug(
                "The following dependencies were added to '%s': %s", file, str_list
            )
        else:
            logger.debug("The following dependencies could not be added: %s", str_list)


def run(original_args) -> int:
    start = datetime.datetime.now()

    codemod_registry = registry.load_registered_codemods()

    # A little awkward, but we need the codemod registry in order to validate potential arguments
    argv = parse_args(original_args, codemod_registry)
    if not os.path.exists(argv.directory):
        logger.error(
            "given directory '%s' doesn't exist or can’t be read",
            argv.directory,
        )
        return 1

    configure_logger(argv.verbose, argv.log_format, argv.project_name)

    log_section("startup")
    logger.info("codemodder: python/%s", __version__)
    logger.info("command: %s %s", Path(sys.argv[0]).name, " ".join(original_args))

    tool_result_files_map = {"sonar": argv.sonar_issues_json}
    # TODO find the tool name in the --sarif files here and populate the dict

    repo_manager = PythonRepoManager(Path(argv.directory))
    context = CodemodExecutionContext(
        Path(argv.directory),
        argv.dry_run,
        argv.verbose,
        codemod_registry,
        repo_manager,
        argv.path_include,
        argv.path_exclude,
        tool_result_files_map,
        argv.max_workers,
    )

    repo_manager.parse_project()

    # TODO: this should be a method of CodemodExecutionContext
    codemods_to_run = codemod_registry.match_codemods(
        argv.codemod_include,
        argv.codemod_exclude,
        sast_only=argv.sonar_issues_json or argv.sarif,
    )

    log_section("setup")
    log_list(logging.INFO, "running", codemods_to_run, predicate=lambda c: c.id)
    log_list(logging.INFO, "including paths", argv.path_include)
    log_list(logging.INFO, "excluding paths", argv.path_exclude)

    files_to_analyze: list[Path] = match_files(
        context.directory, argv.path_exclude, argv.path_include
    )

    full_names = [str(path) for path in files_to_analyze]
    log_list(logging.DEBUG, "matched files", full_names)

    semgrep_results: ResultSet = find_semgrep_results(
        context,
        codemods_to_run,
        files_to_analyze,
    )

    apply_codemods(
        context,
        codemods_to_run,
        semgrep_results,
        files_to_analyze,
    )

    results = context.compile_results(codemods_to_run)

    elapsed = datetime.datetime.now() - start
    elapsed_ms = int(elapsed.total_seconds() * 1000)

    if argv.output:
        report_default(elapsed_ms, argv, original_args, results)

    log_report(context, argv, elapsed_ms, files_to_analyze)
    return 0


def main():
    sys_argv = sys.argv[1:]
    sys.exit(run(sys_argv))
