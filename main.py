import argparse
import libcst as cst
import sys


def parse_files(file_paths):
    modules = []
    # for path in file_paths:
    with open(file_paths, "r") as f:
        code = f.read()
        try:
            cst_mod = cst.parse_module(code)
            breakpoint()
            modules.append(cst_mod)
        except cst.CSTParseError as e:
            # Handle parse errors
            pass
    return modules


def analyze(parsed):
    pass


def main():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("files")

    argv = parser.parse_args()
    breakpoint()
    parsed = parse_files(argv.files)

    # pixee = Pixee()
    # results = pixee.run_with_args(args)


if __name__ == "__main__":
    sys.exit(main())
