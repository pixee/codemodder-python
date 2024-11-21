import datetime
import itertools
import logging
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import DefaultDict, Sequence

from codemodder import __version__, providers, registry
from codemodder.cli import parse_args
from codemodder.codemods.api import BaseCodemod
from codemodder.codemods.semgrep import SemgrepRuleDetector
from codemodder.codetf import CodeTF
from codemodder.context import CodemodExecutionContext
from codemodder.dependency import Dependency
from codemodder.llm import MisconfiguredAIClient
from codemodder.logging import configure_logger, log_list, log_section, logger
from codemodder.project_analysis.file_parsers.package_store import PackageStore
from codemodder.project_analysis.python_repo_manager import PythonRepoManager
from codemodder.result import ResultSet
from codemodder.sarifs import detect_sarif_tools
from codemodder.semgrep import run as run_semgrep


def find_semgrep_results(
    context: CodemodExecutionContext,
    codemods: Sequence[BaseCodemod],
    files_to_analyze: list[Path] | None = None,
) -> ResultSet:
    """Run semgrep once with all configuration files from all codemods and return a set of applicable rule IDs"""
    if not (
        yaml_files := list(
            itertools.chain.from_iterable(
                [
                    codemod.detector.get_yaml_files(codemod._internal_name)
                    for codemod in codemods
                    if codemod.detector
                    and isinstance(codemod.detector, SemgrepRuleDetector)
                ]
            )
        )
    ):
        return ResultSet()

    return run_semgrep(context, yaml_files, files_to_analyze)


def log_report(context, output, elapsed_ms, files_to_analyze):
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
    logger.info("report file: %s", output)
    logger.info("total elapsed: %s ms", elapsed_ms)
    logger.info("  semgrep:     %s ms", context.timer.get_time_ms("semgrep"))
    logger.info("  parse:       %s ms", context.timer.get_time_ms("parse"))
    logger.info("  transform:   %s ms", context.timer.get_time_ms("transform"))
    logger.info("  write:       %s ms", context.timer.get_time_ms("write"))


def apply_codemods(
    context: CodemodExecutionContext,
    codemods_to_run: Sequence[BaseCodemod],
):
    log_section("scanning")

    if not context.files_to_analyze:
        logger.info("no files to scan")
        return

    if not codemods_to_run:
        logger.info("no codemods to run")
        return

    # run codemods one at a time making sure to respect the given sequence
    for codemod in codemods_to_run:
        # NOTE: this may be used as a progress indicator by upstream tools
        logger.info("running codemod %s", codemod.id)
        codemod.apply(context)
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


def run(
    directory: Path | str,
    dry_run: bool,
    output: Path | str | None = None,
    output_format: str = "codetf",
    verbose: bool = False,
    tool_result_files_map: DefaultDict[str, list[Path]] = defaultdict(list),
    path_include: list[str] | None = None,
    path_exclude: list[str] | None = None,
    codemod_include: list[str] | None = None,
    codemod_exclude: list[str] | None = None,
    max_workers: int = 1,
    original_cli_args: list[str] | None = None,
    codemod_registry: registry.CodemodRegistry | None = None,
    sast_only: bool = False,
    ai_client: bool = True,
) -> tuple[CodeTF | None, int]:
    start = datetime.datetime.now()

    codemod_registry = codemod_registry or registry.load_registered_codemods()

    path_include = path_include or []
    path_exclude = path_exclude or []
    codemod_include = codemod_include or []
    codemod_exclude = codemod_exclude or []

    provider_registry = providers.load_providers()

    log_section("startup")
    logger.info("codemodder: python/%s", __version__)

    for file_name in itertools.chain(*tool_result_files_map.values()):
        if not os.path.exists(file_name):
            logger.error(
                f"FileNotFoundError: [Errno 2] No such file or directory: '{file_name}'"
            )
            return None, 1

    repo_manager = PythonRepoManager(Path(directory))

    try:
        context = CodemodExecutionContext(
            Path(directory),
            dry_run,
            verbose,
            codemod_registry,
            provider_registry,
            repo_manager,
            path_include,
            path_exclude,
            tool_result_files_map,
            max_workers,
            ai_client,
        )
    except MisconfiguredAIClient as e:
        logger.error(e)
        return None, 3  # Codemodder instructions conflicted (according to spec)

    context.repo_manager.parse_project()

    # TODO: this should be a method of CodemodExecutionContext
    codemods_to_run = codemod_registry.match_codemods(
        codemod_include,
        codemod_exclude,
        sast_only=sast_only,
    )

    log_section("setup")
    log_list(logging.INFO, "running", codemods_to_run, predicate=lambda c: c.id)
    log_list(logging.INFO, "including paths", context.included_paths)
    log_list(logging.INFO, "excluding paths", path_exclude)

    log_list(
        logging.DEBUG, "matched files", (str(path) for path in context.files_to_analyze)
    )

    context.semgrep_prefilter_results = find_semgrep_results(
        context,
        codemods_to_run,
        context.find_and_fix_paths,
    )

    apply_codemods(
        context,
        codemods_to_run,
    )

    elapsed = datetime.datetime.now() - start
    elapsed_ms = int(elapsed.total_seconds() * 1000)

    logger.debug("Output format %s", output_format)
    codetf = CodeTF.build(
        context,
        elapsed_ms,
        original_cli_args or [],
        context.compile_results(codemods_to_run),
    )
    if output:
        codetf.write_report(output)

    log_report(
        context,
        output,
        elapsed_ms,
        [] if not codemods_to_run else context.files_to_analyze,
    )
    return codetf, 0


def _run_cli(original_args) -> int:
    codemod_registry = registry.load_registered_codemods()
    argv = parse_args(original_args, codemod_registry)
    if not os.path.exists(argv.directory):
        logger.error(
            "given directory '%s' doesn't exist or can’t be read",
            argv.directory,
        )
        return 1

    try:
        tool_result_files_map: DefaultDict[str, list[Path]] = detect_sarif_tools(
            [Path(name) for name in argv.sarif or []]
        )
    except FileNotFoundError as err:
        logger.error(err)
        return 1

    tool_result_files_map["sonar"].extend(argv.sonar_issues_json or [])
    tool_result_files_map["sonar"].extend(argv.sonar_hotspots_json or [])
    tool_result_files_map["defectdojo"].extend(argv.defectdojo_findings_json or [])

    logger.info("command: %s %s", Path(sys.argv[0]).name, " ".join(original_args))
    configure_logger(argv.verbose, argv.log_format, argv.project_name)

    _, status = run(
        argv.directory,
        argv.dry_run,
        argv.output,
        argv.output_format,
        argv.verbose,
        tool_result_files_map,
        argv.path_include,
        argv.path_exclude,
        argv.codemod_include,
        argv.codemod_exclude,
        max_workers=argv.max_workers,
        original_cli_args=original_args,
        codemod_registry=codemod_registry,
        sast_only=argv.sonar_issues_json or argv.sarif,
    )
    return status


def main():
    sys_argv = sys.argv[1:]
    sys.exit(_run_cli(sys_argv))
