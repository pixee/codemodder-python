import datetime
import difflib
import os
import sys
from pathlib import Path
import libcst as cst
from libcst.codemod import CodemodContext
from codemodder.file_context import FileContext

from codemodder.logging import logger
from codemodder.cli import parse_args
from codemodder.code_directory import file_line_patterns, match_files
from codemodder.codemods import match_codemods
from codemodder.codemods.change import Change
from codemodder.dependency_manager import DependencyManager
from codemodder.report.codetf_reporter import report_default
from codemodder.semgrep import run as semgrep_run
from codemodder.sarifs import parse_sarif_files

# Must use from import here to point to latest state
from codemodder import global_state

RESULTS_BY_CODEMOD = []
from dataclasses import dataclass


@dataclass
class ChangeSet:
    """A set of changes made to a file at `path`"""

    path: str
    diff: str
    changes: list[Change]

    def to_json(self):
        return {"path": self.path, "diff": self.diff, "changes": self.changes}


def update_code(file_path, new_code):
    """
    Write the `new_code` to the `file_path`
    """
    logger.info("Updated file %s", file_path)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_code)


def run_codemods_for_file(
    file_context,
    codemods_to_run,
    source_tree,
):
    for name, codemod_kls in codemods_to_run.items():
        wrapper = cst.MetadataWrapper(source_tree)
        codemod = codemod_kls(
            CodemodContext(wrapper=wrapper),
            file_context,
        )
        if not codemod.should_transform:
            continue

        logger.info("Running codemod %s for %s", name, file_context.file_path)
        output_tree = codemod.transform_module(source_tree)
        changed_file = not output_tree.deep_equals(source_tree)

        if changed_file:
            diff = "".join(
                difflib.unified_diff(
                    source_tree.code.splitlines(1), output_tree.code.splitlines(1)
                )
            )
            logger.debug("CHANGED %s with codemod %s", file_context.file_path, name)
            logger.debug(diff)

            codemod_kls.CHANGESET_ALL_FILES.append(
                ChangeSet(
                    str(file_context.file_path),
                    diff,
                    changes=file_context.codemod_changes,
                ).to_json()
            )
            if file_context.dry_run:
                logger.info("Dry run, not changing files")
            else:
                update_code(file_context.file_path, output_tree.code)


def analyze_files(
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
            cli_args.dry_run,
            line_exclude,
            line_include,
            sarif_for_file,
        )

        run_codemods_for_file(
            file_context,
            codemods_to_run,
            source_tree,
        )


def compile_results(codemods):
    for name, codemod_kls in codemods.items():
        if not codemod_kls.CHANGESET_ALL_FILES:
            continue
        data = {
            "codemod": f"pixee:python/{name}",
            "summary": codemod_kls.METADATA.DESCRIPTION,
            "references": [],
            "properties": {},
            "failedFiles": [],
            "changeset": codemod_kls.CHANGESET_ALL_FILES,
        }

        RESULTS_BY_CODEMOD.append(data)


def run(argv, original_args) -> int:
    start = datetime.datetime.now()

    if not os.path.exists(argv.directory):
        # project directory doesn't exist or can’t be read
        return 1

    global_state.set_directory(Path(argv.directory))

    codemods_to_run = match_codemods(argv.codemod_include, argv.codemod_exclude)
    if not codemods_to_run:
        # We only currently have semgrep codemods so don't go on if no codemods matched.
        logger.warning("No codemods to run")
        return 0

    logger.debug("Codemods to run: %s", codemods_to_run)

    # parse sarifs from --sarif flags
    sarif_results = parse_sarif_files(argv.sarif or [])

    # run semgrep and gather the results
    semgrep_results = semgrep_run(codemods_to_run)

    # merge the results
    sarif_results.update(semgrep_results)

    if not sarif_results:
        logger.warning("No sarif results.")

    files_to_analyze = match_files(
        global_state.DIRECTORY, argv.path_exclude, argv.path_include
    )
    if not files_to_analyze:
        logger.warning("No files matched.")
        return 0

    full_names = [str(path) for path in files_to_analyze]
    logger.debug("Matched files:\n%s", "\n".join(full_names))

    analyze_files(
        files_to_analyze,
        codemods_to_run,
        sarif_results,
        argv,
    )

    compile_results(codemods_to_run)

    DependencyManager().write(dry_run=argv.dry_run)
    elapsed = datetime.datetime.now() - start
    elapsed_ms = int(elapsed.total_seconds() * 1000)
    report_default(elapsed_ms, argv, original_args, RESULTS_BY_CODEMOD)
    return 0


if __name__ == "__main__":
    sys_argv = sys.argv[1:]
    sys.exit(run(parse_args(sys_argv), sys_argv))
