import os
import sys
import libcst as cst
import logging

from libcst.codemod import CodemodContext
from codemodder.cli import parse_args
from codemodder.code_directory import match_files
from codemodder.codemods import CODEMODS


def write_report(report, outfile):
    # Move this func to an instance of `report`
    try:
        with open(outfile, "w") as output_f:
            output_f.write(report)
    except Exception:
        # Any issues with writing the output file should exit status 2.
        return 2


def run(argv) -> int:
    if not os.path.exists(argv.directory):
        # project directory doesn't exist or can’t be read
        return 1

    files_to_analyze = match_files(argv.directory, argv.path_exclude, argv.path_include)
    changed_files = {}

    # some codemods take raw file paths, others need parsed CST
    for file_path in files_to_analyze:
        changed_file = False

        if not os.path.exists(file_path):
            print(f"Error: file '{file_path}' does not exist")
            continue

        # for codemod in codemods:
        # if codemod.needs_raw_file:
        # codemod.run(file_path)
        # changed_file = True

        # get CST for codemods that need CST
        with open(file_path, "r") as f:
            code = f.read()

        try:
            input_tree = cst.parse_module(code)
            print("*** ORIGINAL:")
            print(input_tree.code)
        except Exception as e:
            print(f"Error parsing file '{file_path}': {str(e)}")
            continue
        # for codemod in codemods:
        # if codemod.needs_cst:
        if argv.codemod:
            codemod_kls = CODEMODS.get(argv.codemod)
            command_instance = codemod_kls(CodemodContext())
            output_tree = command_instance.transform_module(input_tree)
            changed_file = True

        # if changed_file:
        #     changed_files.append(file_path)
        if changed_file and not argv.dry_run:
            print("*** CHANGED:")
            print(output_tree.code)
            # diff https://libcst.readthedocs.io/en/latest/tutorial.html
        #     actually write the changes to the file

        if argv.dry_run:
            logging.info("Dry run, not changing files")
            return 0

        # results = CombineResults(changed_files)
        if argv.output_format == "codetf":
            pass
            # report = CodeTF.generate(results, config)
        else:
            pass
        report = ""

        write_report(report, argv.output)

    return 0


if __name__ == "__main__":
    sys.exit(run(parse_args(sys.argv[1:])))
