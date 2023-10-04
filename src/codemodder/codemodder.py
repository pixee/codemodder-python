import datetime
import difflib
import os
import sys
from pathlib import Path
import libcst as cst
from libcst.codemod import CodemodContext
from codemodder.file_context import FileContext

from codemodder import registry
from codemodder.logging import logger
from codemodder.cli import parse_args
from codemodder.code_directory import file_line_patterns, match_files
from codemodder.context import CodemodExecutionContext, ChangeSet
from codemodder.dependency_manager import write_dependencies
from codemodder.executor import CodemodExecutorWrapper
from codemodder.report.codetf_reporter import report_default


def update_code(file_path, new_code):
    """
    Write the `new_code` to the `file_path`
    """
    logger.info("Updated file %s", file_path)
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
        return

    logger.info("Running codemod %s for %s", name, file_context.file_path)
    output_tree = codemod.transform_module(source_tree)
    # TODO: there has got to be a more efficient way to check this?
    changed_file = not output_tree.deep_equals(source_tree)

    if changed_file:
        diff = "".join(
            difflib.unified_diff(
                source_tree.code.splitlines(1), output_tree.code.splitlines(1)
            )
        )
        logger.debug("CHANGED %s with codemod %s", file_context.file_path, name)
        logger.debug(diff)

        change_set = ChangeSet(
            str(file_context.file_path.relative_to(execution_context.directory)),
            diff,
            changes=file_context.codemod_changes,
        )
        execution_context.add_result(name, change_set)

        if execution_context.dry_run:
            logger.info("Dry run, not changing files")
        else:
            update_code(file_context.file_path, output_tree.code)


def analyze_files(
    execution_context: CodemodExecutionContext,
    files_to_analyze,
    codemod,
    sarif,
    cli_args,
):
    for file_path in files_to_analyze:
        # TODO: handle potential race condition that file no longer exists at this point
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        try:
            source_tree = cst.parse_module(code)
        except Exception:
            logger.exception("Error parsing file %s", file_path)
            continue

        line_exclude = file_line_patterns(file_path, cli_args.path_exclude)
        line_include = file_line_patterns(file_path, cli_args.path_include)
        sarif_for_file = sarif.get(str(file_path)) or {}

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


def run(original_args) -> int:
    start = datetime.datetime.now()

    codemod_registry = registry.load_registered_codemods()

    # A little awkward, but we need the codemod registry in order to validate potential arguments
    argv = parse_args(original_args, codemod_registry)
    if not os.path.exists(argv.directory):
        logger.error(
            "Given directory '%s' doesn't exist or can’t be read",
            argv.directory,
        )
        return 1

    context = CodemodExecutionContext(
        Path(argv.directory),
        # TODO: pass all of argv instead of just dry_run
        argv.dry_run,
        codemod_registry,
    )

    # TODO: this should be a method of CodemodExecutionContext
    codemods_to_run = codemod_registry.match_codemods(
        argv.codemod_include, argv.codemod_exclude
    )
    if not codemods_to_run:
        # We only currently have semgrep codemods so don't go on if no codemods matched.
        logger.warning("No codemods to run")
        return 0

    logger.debug("Codemods to run: %s", [codemod.id for codemod in codemods_to_run])

    # XXX: sarif files given on the command line are currently not used by any codemods

    files_to_analyze = match_files(
        context.directory, argv.path_exclude, argv.path_include
    )
    if not files_to_analyze:
        logger.warning("No files matched.")
        return 0

    full_names = [str(path) for path in files_to_analyze]
    logger.debug("Matched files:\n%s", "\n".join(full_names))

    # run codemods in sequence
    for codemod in codemods_to_run:
        results = codemod.apply(context)
        analyze_files(
            context,
            files_to_analyze,
            codemod,
            results,
            argv,
        )

    results = context.compile_results(codemods_to_run)

    write_dependencies(context)
    elapsed = datetime.datetime.now() - start
    elapsed_ms = int(elapsed.total_seconds() * 1000)
    report_default(elapsed_ms, argv, original_args, results)
    return 0


def main():
    sys_argv = sys.argv[1:]
    sys.exit(run(sys_argv))
