import argparse
import glob
import os
import sys
import libcst as cst

from libcst.codemod import CodemodContext
from codemods.secure_random import SecureRandom
from libcst.codemod._runner import transform_module


def find_files(parent_path):
    # todo: convert to class and add includes, excludes
    matching_files = []
    for file_path in glob.glob(f"{parent_path}/*.py", recursive=True):
        matching_files.append(file_path)
    return matching_files


def run(argv):

    paths_to_analyze = find_files(argv.directory)
    codemods = []  # secure_randomness, semgrep, etc
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
        except Exception as e:
            print(f"Error parsing file '{file_path}': {str(e)}")
            continue
        # for codemod in codemods:
        # if codemod.needs_cst:
        command_instance = SecureRandom(CodemodContext())  # **codemod_args)
        result = transform_module(command_instance, code)
        output_tree = command_instance.transform_module(input_tree)
        # changed_file = True

        # if changed_file:
        #     changed_files.append(file_path)
        # if changed_file and not args.dry_run:
        #     actually write the changes to the file

        # if args.dry_run:
        #     logger.info("Dry run, not changing files")
        # results = CombineResults(changed_files)
        # report = CodeTF.generate(results, config)


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_help(sys.stderr)
        sys.exit(message)


def parse_args(argv):
    parser = ArgumentParser(description="Run codemods and change code.")
    parser.add_argument("directory", type=str, help="path to find files")
    parser.add_argument(
        "output", type=str, help="name of output file to produce", default="stdout"
    )
    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        help="do everything except make changes to files",
    )
    # todo: includes, exludes

    return parser.parse_args(argv)


if __name__ == "__main__":
    run(parse_args(sys.argv[1:]))
