import glob
import os
import sys
import libcst as cst

from libcst.codemod import CodemodContext
from codemodder.cli import parse_args
from codemodder.codemods import CODEMODS


def find_files(parent_path):
    # todo: convert to class and add includes, excludes
    matching_files = []
    for file_path in glob.glob(f"{parent_path}/*.py", recursive=True):
        matching_files.append(file_path)
    return matching_files


def run(argv):
    paths_to_analyze = find_files(argv.directory)
    changed_files = {}
    # some codemods take raw file paths, others need parsed CST
    for file_path in paths_to_analyze:
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

        # if argv.dry_run:
        #     logger.info("Dry run, not changing files")
        # results = CombineResults(changed_files)
        # report = CodeTF.generate(results, config)


if __name__ == "__main__":
    run(parse_args(sys.argv[1:]))
