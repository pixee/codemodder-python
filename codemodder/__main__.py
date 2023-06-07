import datetime
import difflib
import os
import sys
import libcst as cst


from libcst.codemod import CodemodContext
from codemodder.logging import logger
from codemodder.cli import parse_args
from codemodder.code_directory import match_files
from codemodder.codemods import match_codemods
from codemodder.report.codetf_reporter import report_default
from codemodder.semgrep import run as semgrep_run

RESULTS_BY_CODEMOD = []
from dataclasses import dataclass


@dataclass
class Change:
    lineNumber: str
    description: str
    properties: dict
    packageActions: list


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
    print(f"Updated file {file_path}")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_code)


def run_codemods_for_file(file_path, codemods_to_run, source_tree, dry_run):
    for name, codemod_kls in codemods_to_run.items():
        logger.info("Running codemod %s", name)
        command_instance = codemod_kls(CodemodContext())
        output_tree = command_instance.transform_module(source_tree)
        changed_file = not output_tree.deep_equals(source_tree)

        if changed_file:
            diff = "".join(
                difflib.unified_diff(
                    source_tree.code.splitlines(1), output_tree.code.splitlines(1)
                )
            )
            print(f"*** CHANGED {file_path} with codemod {name}:")
            print(diff)
            codemod_kls.CHANGESET.append(
                ChangeSet(str(file_path), diff, changes=[]).to_json()
            )
            if dry_run:
                logger.info("Dry run, not changing files")
            else:
                update_code(file_path, output_tree.code)


def run(argv, original_args) -> int:
    start = datetime.datetime.now()

    if not os.path.exists(argv.directory):
        # project directory doesn't exist or can’t be read
        return 1

    # mock this in some tests to speed unit tests up
    semgrep_run()

    files_to_analyze = match_files(argv.directory, argv.path_exclude, argv.path_include)
    if not files_to_analyze:
        logger.warning("No files matched.")
        return 0

    full_names = [str(path) for path in files_to_analyze]
    logger.debug("Matched files:\n%s", "\n".join(full_names))

    codemods_to_run = match_codemods(argv.codemod_include, argv.codemod_exclude)

    for file_path in files_to_analyze:
        # TODO: handle potential race condition that file no longer exists at this point
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        try:
            source_tree = cst.parse_module(code)
        except Exception as e:
            print(f"Error parsing file '{file_path}': {str(e)}")
            continue

        run_codemods_for_file(file_path, codemods_to_run, source_tree, argv.dry_run)

    for name, codemod_kls in codemods_to_run.items():
        if not codemod_kls.CHANGESET:
            continue
        data = {
            "codemod": f"pixee:python/{name}",
            "summary": codemod_kls.DESCRIPTION,
            "references": [],
            "properties": {},
            "failedFiles": [],
            "changeset": codemod_kls.CHANGESET,
        }

        RESULTS_BY_CODEMOD.append(data)
    elapsed = datetime.datetime.now() - start
    elapsed_ms = int(elapsed.total_seconds() * 1000)
    report_default(elapsed_ms, argv, original_args, RESULTS_BY_CODEMOD)
    return 0


if __name__ == "__main__":
    sys_argv = sys.argv[1:]
    sys.exit(run(parse_args(sys_argv), sys_argv))
