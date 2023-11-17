from concurrent.futures import ThreadPoolExecutor
import datetime
import itertools
import logging
import os
import sys
from pathlib import Path

import libcst as cst
from libcst.codemod import CodemodContext
from codemodder.file_context import FileContext

from codemodder import registry, __version__
from codemodder.logging import configure_logger, logger, log_section, log_list
from codemodder.cli import parse_args
from codemodder.change import ChangeSet
from codemodder.code_directory import file_line_patterns, match_files
from codemodder.context import CodemodExecutionContext
from codemodder.diff import create_diff as create_diff_from_lines
from codemodder.executor import CodemodExecutorWrapper
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
    codemods: list[CodemodExecutorWrapper],
) -> ResultSet:
    """Run semgrep once with all configuration files from all codemods and return a set of applicable rule IDs"""
    yaml_files = list(
        itertools.chain.from_iterable(
            [codemod.yaml_files for codemod in codemods if codemod.yaml_files]
        )
    )
    if not yaml_files:
        return ResultSet()

    return run_semgrep(context, yaml_files)


def create_diff(original_tree: cst.Module, new_tree: cst.Module) -> str:
    """
    Create a diff between the original and output trees.
    """
    return create_diff_from_lines(
        original_tree.code.splitlines(keepends=True),
        new_tree.code.splitlines(keepends=True),
    )


def apply_codemod_to_file(
    base_directory: Path,
    file_context,
    codemod_kls: CodemodExecutorWrapper,
    source_tree,
    dry_run: bool = False,
):
    wrapper = cst.MetadataWrapper(source_tree)
    codemod = codemod_kls(CodemodContext(wrapper=wrapper), file_context)
    if not codemod.should_transform:
        return False

    with file_context.timer.measure("transform"):
        output_tree = codemod.transform_module(source_tree)

    # TODO: we can probably just use the presence of recorded changes instead of
    # comparing the trees to gain some efficiency
    if output_tree.deep_equals(source_tree):
        return False

    diff = create_diff(source_tree, output_tree)
    change_set = ChangeSet(
        str(file_context.file_path.relative_to(base_directory)),
        diff,
        changes=file_context.codemod_changes,
    )
    file_context.add_result(change_set)

    if not dry_run:
        with file_context.timer.measure("write"):
            update_code(file_context.file_path, output_tree.code)

    return True


def process_file(
    idx: int,
    file_path: Path,
    base_directory: Path,
    codemod,
    results: ResultSet,
    cli_args,
):  # pylint: disable=too-many-arguments
    logger.debug("scanning file %s", file_path)
    if idx and idx % 100 == 0:
        logger.info("scanned %s files...", idx)  # pragma: no cover

    line_exclude = file_line_patterns(file_path, cli_args.path_exclude)
    line_include = file_line_patterns(file_path, cli_args.path_include)
    findings_for_rule = results.results_for_rule_and_file(
        codemod.name,  # TODO: should be full ID
        file_path,
    )

    file_context = FileContext(
        base_directory,
        file_path,
        line_exclude,
        line_include,
        findings_for_rule,
    )

    try:
        with file_context.timer.measure("parse"):
            with open(file_path, "r", encoding="utf-8") as f:
                source_tree = cst.parse_module(f.read())
    except Exception:
        file_context.add_failure(file_path)
        logger.exception("error parsing file %s", file_path)
        return file_context

    apply_codemod_to_file(
        base_directory,
        file_context,
        codemod,
        source_tree,
        cli_args.dry_run,
    )

    return file_context


def analyze_files(
    execution_context: CodemodExecutionContext,
    files_to_analyze,
    codemod,
    results: ResultSet,
    cli_args,
):
    with ThreadPoolExecutor(max_workers=cli_args.max_workers) as executor:
        logger.debug(
            "using executor with %s threads",
            cli_args.max_workers,
        )
        analysis_results = executor.map(
            lambda args: process_file(
                args[0],
                args[1],
                execution_context.directory,
                codemod,
                results,
                cli_args,
            ),
            enumerate(files_to_analyze),
        )
        executor.shutdown(wait=True)
        execution_context.process_results(codemod.id, analysis_results)


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
    codemods_to_run: list[CodemodExecutorWrapper],
    semgrep_results: ResultSet,
    files_to_analyze: list[Path],
    argv,
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
        # Unfortunately the IDs from semgrep are not fully specified
        # TODO: eventually we need to be able to use fully specified IDs here
        if codemod.is_semgrep and codemod.name not in semgrep_finding_ids:
            logger.debug(
                "no results from semgrep for %s, skipping analysis",
                codemod.id,
            )
            continue

        logger.info("running codemod %s", codemod.id)
        semgrep_files = semgrep_results.files_for_rule(codemod.name)
        # Non-semgrep codemods ignore the semgrep results
        results = codemod.apply(context, semgrep_files)
        analyze_files(
            context,
            files_to_analyze,
            codemod,
            results,
            argv,
        )
        context.process_dependencies(codemod.id)
        context.log_changes(codemod.id)


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

    repo_manager = PythonRepoManager(Path(argv.directory))
    context = CodemodExecutionContext(
        Path(argv.directory),
        argv.dry_run,
        argv.verbose,
        codemod_registry,
        repo_manager,
    )
    # todo: enable when ready
    # repo_manager.package_stores

    # TODO: this should be a method of CodemodExecutionContext
    codemods_to_run = codemod_registry.match_codemods(
        argv.codemod_include, argv.codemod_exclude
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

    semgrep_results: ResultSet = find_semgrep_results(context, codemods_to_run)

    apply_codemods(
        context,
        codemods_to_run,
        semgrep_results,
        files_to_analyze,
        argv,
    )

    results = context.compile_results(codemods_to_run)

    elapsed = datetime.datetime.now() - start
    elapsed_ms = int(elapsed.total_seconds() * 1000)
    report_default(elapsed_ms, argv, original_args, results)

    log_report(context, argv, elapsed_ms, files_to_analyze)
    return 0


def main():
    sys_argv = sys.argv[1:]
    sys.exit(run(sys_argv))
