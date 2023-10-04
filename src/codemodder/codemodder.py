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
from codemodder.report.codetf_reporter import report_default
from codemodder.semgrep import run as semgrep_run
from codemodder.sarifs import parse_sarif_files


def update_code(file_path, new_code):
    """
    Write the `new_code` to the `file_path`
    """
    logger.info("Updated file %s", file_path)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_code)


def run_codemods_for_file(
    execution_context: CodemodExecutionContext,
    file_context,
    codemods_to_run,
    source_tree,
):
    for name, codemod_kls in codemods_to_run.items():
        wrapper = cst.MetadataWrapper(source_tree)
        codemod = codemod_kls(
            CodemodContext(wrapper=wrapper),
            execution_context,
            file_context,
        )
        if not codemod.should_transform:
            continue

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
    codemods_to_run,
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
        sarif_for_file = sarif[str(file_path)]

        file_context = FileContext(
            file_path,
            line_exclude,
            line_include,
            sarif_for_file,
        )

        run_codemods_for_file(
            execution_context,
            file_context,
            codemods_to_run,
            source_tree,
        )


def compile_results(execution_context: CodemodExecutionContext, codemods):
    results = []
    for name, codemod in codemods.items():
        if not (changeset := execution_context.results_by_codemod.get(name)):
            continue

        data = {
            "codemod": codemod.id,
            "summary": codemod.summary,
            "description": codemod.description,
            "references": [],
            "properties": {},
            "failedFiles": [],
            "changeset": [change.to_json() for change in changeset],
        }

        results.append(data)

    return results


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
        argv.dry_run,
        codemod_registry,
    )

    codemods_to_run = codemod_registry.match_codemods(
        argv.codemod_include, argv.codemod_exclude
    )
    if not codemods_to_run:
        # We only currently have semgrep codemods so don't go on if no codemods matched.
        logger.warning("No codemods to run")
        return 0

    logger.debug("Codemods to run: %s", codemods_to_run)

    # parse sarifs from --sarif flags
    sarif_results = parse_sarif_files(argv.sarif or [])

    # run semgrep and gather the results
    # TODO: call once per codemod rather than once for all codemods
    semgrep_results = semgrep_run(context, codemods_to_run)

    # merge the results
    sarif_results.update(semgrep_results)

    if not sarif_results:
        logger.warning("No sarif results.")

    files_to_analyze = match_files(
        context.directory, argv.path_exclude, argv.path_include
    )
    if not files_to_analyze:
        logger.warning("No files matched.")
        return 0

    full_names = [str(path) for path in files_to_analyze]
    logger.debug("Matched files:\n%s", "\n".join(full_names))

    analyze_files(
        context,
        files_to_analyze,
        codemods_to_run,
        sarif_results,
        argv,
    )

    results = compile_results(context, codemods_to_run)

    write_dependencies(context)
    elapsed = datetime.datetime.now() - start
    elapsed_ms = int(elapsed.total_seconds() * 1000)
    report_default(elapsed_ms, argv, original_args, results)
    return 0


def main():
    # TODO: I'm not sure why this needs to be parsed out separately
    # Maybe it has something to do with the invocation as python -m codemodder.
    sys_argv = sys.argv[1:]
    sys.exit(run(sys_argv))
