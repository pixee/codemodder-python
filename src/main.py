import argparse
import glob
import os
import sys
import libcst as cst

from libcst.codemod import CodemodContext
from src.codemods.secure_random import SecureRandom
from src.codemods.url_sandbox import UrlSandbox
from src import __VERSION__

CODEMODS = {"secure_random": SecureRandom, "url_sandbox": UrlSandbox}


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


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_help(sys.stderr)
        sys.exit(message)


def parse_args(argv):
    parser = ArgumentParser(description="Run codemods and change code.")
    parser.add_argument("--version", action="version", version=__VERSION__)

    parser.add_argument("directory", type=str, help="path to find files")
    parser.add_argument(
        "output", type=str, help="name of output file to produce", default="stdout"
    )
    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        help="do everything except make changes to files",
    )
    parser.add_argument("--codemod", type=str, help="name of codemod to run")
    # todo: includes, exludes

    return parser.parse_args(argv)


if __name__ == "__main__":
    run(parse_args(sys.argv[1:]))
