import datetime
import os
import sys
import libcst as cst


from libcst.codemod import CodemodContext
from codemodder.logging import logger
from codemodder.cli import parse_args
from codemodder.code_directory import match_files
from codemodder.codemods import match_codemods
from codemodder.report.codetf_reporter import report_default


def run_codemods_for_file(file_path, codemods_to_run, source_tree, dry_run):
    print("*** ORIGINAL:")
    print(source_tree.code)

    for name, codemod_kls in codemods_to_run.items():
        logger.info("Running codemod %s", name)
        command_instance = codemod_kls(CodemodContext())
        output_tree = command_instance.transform_module(source_tree)
        changed_file = not output_tree.deep_equals(source_tree)

        if changed_file:
            print(f"*** CHANGED with {name}:")
            print(output_tree.code)

            if dry_run:
                logger.info("Dry run, not changing files")
            else:
                print(f"Updated file {file_path}")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(output_tree.code)


def run(argv, original_args) -> int:
    start = datetime.datetime.now()

    if not os.path.exists(argv.directory):
        # project directory doesn't exist or can’t be read
        return 1

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

        elapsed = datetime.datetime.now() - start
        elapsed_ms = int(elapsed.total_seconds() * 1000)
        report_default(elapsed_ms, argv, original_args)
    return 0


if __name__ == "__main__":
    sys_argv = sys.argv[1:]
    sys.exit(run(parse_args(sys_argv), sys_argv))
