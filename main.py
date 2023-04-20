import argparse
import json
import os
import sys

import libcst as cst


def find_insecure_random_calls(tree):
    """
    Given a CST node tree, finds any calls to the `random.random()` function,
    which is known to be cryptographically insecure.
    """
    for node in tree.find_all(cst.Name):
        if node.value == "random":
            parent = node.parent
            if isinstance(parent, cst.Call) and parent.func == node:
                grandparent = parent.parent
                if isinstance(grandparent, cst.Expr) and isinstance(
                    grandparent.parent, cst.Module
                ):
                    yield grandparent


def main():
    parser = argparse.ArgumentParser(description="Run codemods and change code.")
    parser.add_argument(
        "directory", metavar="file", type=str, nargs="+", help="path to find files"
    )
    # dry run
    # output path, for now just print to stdout
    args = parser.parse_args()

    paths_to_analyze = (
        []
    )  # FileFinder(parser.directory) # pass in all includes/excludes
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
            tree = cst.parse_module(code)
        except Exception as e:
            print(f"Error parsing file '{file_path}': {str(e)}")
            continue

        # for codemod in codemods:
        # if codemod.needs_cst:
        # codemod.run(tree)
        # changed_file = True

        # if changed_file:
        #     changed_files.append(file_path)
        # if changed_file and not args.dry_run:
        #     actually write the changes to the file

        # if args.dry_run:
        #     logger.info("Dry run, not changing files")
        # results = CombineResults(changed_files)
        # report = CodeTF.generate(results, config)


if __name__ == "__main__":
    main()
