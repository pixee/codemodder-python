import datetime
import difflib
import logging
import os
import sys
from textwrap import indent

import libcst as cst
from libcst.codemod import CodemodContext
from codemodder.file_context import FileContext

from codemodder import registry, __VERSION__
from codemodder.logging import configure_logger, logger, log_section, log_list
from codemodder.cli import parse_args
from codemodder.change import ChangeSet
from codemodder.code_directory import file_line_patterns, match_files
from codemodder.context import CodemodExecutionContext
from codemodder.executor import CodemodExecutorWrapper
from codemodder.report.codetf_reporter import report_default


def update_code(file_path, new_code):
    """
    Write the `new_code` to the `file_path`
    """
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_code)


def apply_codemod_to_file(
    execution_context: CodemodExecutionContext,
    file_context,
    codemod_kls: CodemodExecutorWrapper,
    source_tree,
):
    name = codemod_kls.id
    wrapper = cst.MetadataWrapper(source_tree)
    codemod = codemod_kls(
        CodemodContext(wrapper=wrapper),
        execution_context,
        file_context,
    )
    if not codemod.should_transform:
        return False

    output_tree = codemod.transform_module(source_tree)
    # TODO: we can probably just use the presence of recorded changes instead of
    # comparing the trees to gain some efficiency
    if output_tree.deep_equals(source_tree):
        return False

    diff = "".join(
        difflib.unified_diff(
            source_tree.code.splitlines(1), output_tree.code.splitlines(1)
        )
    )

    change_set = ChangeSet(
        str(file_context.file_path.relative_to(execution_context.directory)),
        diff,
        changes=file_context.codemod_changes,
    )
    execution_context.add_result(name, change_set)

    if not execution_context.dry_run:
        update_code(file_context.file_path, output_tree.code)

    return True


def analyze_files(
    execution_context: CodemodExecutionContext,
    files_to_analyze,
    codemod,
    sarif,
    cli_args,
):
    # TODO: parallelize this loop
    for idx, file_path in enumerate(files_to_analyze):
        logger.debug("scanning file %s", file_path)
        if idx and idx % 100 == 0:
            logger.info("scanned %s files...", idx)  # pragma: no cover

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source_tree = cst.parse_module(f.read())
        except Exception:
            execution_context.add_failure(codemod.id, file_path)
            logger.exception("error parsing file %s", file_path)
            continue

        line_exclude = file_line_patterns(file_path, cli_args.path_exclude)
        line_include = file_line_patterns(file_path, cli_args.path_include)
        sarif_for_file = sarif.get(str(file_path)) or {}

        # NOTE: file context will become more important if/when we parallelize this loop
        file_context = FileContext(
            file_path,
            line_exclude,
            line_include,
            sarif_for_file,
        )

        apply_codemod_to_file(
            execution_context,
            file_context,
            codemod,
            source_tree,
        )

        execution_context.add_dependencies(codemod.id, file_context.dependencies)


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
    logger.info("codemodder: python/%s", __VERSION__)
    context = CodemodExecutionContext(argv, codemod_registry)

    # TODO: this should be a method of CodemodExecutionContext
    codemods_to_run = codemod_registry.match_codemods(
        argv.codemod_include, argv.codemod_exclude
    )
    if not codemods_to_run:
        # XXX: sarif files given on the command line are currently not used by any codemods
        logger.error("no codemods to run")
        return 0

    log_section("setup")
    log_list(logging.INFO, "running", codemods_to_run, predicate=lambda c: c.id)
    log_list(logging.INFO, "including paths", argv.path_include)
    log_list(logging.INFO, "excluding paths", argv.path_exclude)

    files_to_analyze = match_files(
        context.directory, argv.path_exclude, argv.path_include
    )
    if not files_to_analyze:
        logger.error("no files matched.")
        return 0

    full_names = [str(path) for path in files_to_analyze]
    logger.debug("matched files:")
    log_list(logging.DEBUG, "matched files", full_names)

    log_section("scanning")
    # run codemods one at a time making sure to respect the given sequence
    for codemod in codemods_to_run:
        logger.info("running codemod %s", codemod.id)
        results = codemod.apply(context)
        analyze_files(
            context,
            files_to_analyze,
            codemod,
            results,
            argv,
        )
        context.process_dependencies(codemod.id)
        context.log_changes(codemod.id)

    results = context.compile_results(codemods_to_run)

    elapsed = datetime.datetime.now() - start
    elapsed_ms = int(elapsed.total_seconds() * 1000)
    report_default(elapsed_ms, argv, original_args, results)

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
    logger.info("elapsed: %s ms", elapsed_ms)

    return 0


def main():
    sys_argv = sys.argv[1:]
    sys.exit(run(sys_argv))
