import os
import sys
import libcst as cst
import logging

from libcst.codemod import CodemodContext
from codemodder.cli import parse_args
from codemodder.code_directory import match_files
from codemodder.codemods import match_codemods


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def write_report(report, outfile):
    # Move this func to an instance of `report`
    try:
        with open(outfile, "w", encoding="utf-8") as output_f:
            output_f.write(report)
    except Exception:
        # Any issues with writing the output file should exit status 2.
        return 2
    return 0


def run(argv) -> int:
    if not os.path.exists(argv.directory):
        # project directory doesn't exist or can’t be read
        return 1

    files_to_analyze = match_files(argv.directory, argv.path_exclude, argv.path_include)
    if not files_to_analyze:
        logging.warning("No files matched.")
        return 0

    full_names = [str(path) for path in files_to_analyze]
    logging.debug("Matched files:\n%s", "\n".join(full_names))

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

        print("*** ORIGINAL:")
        print(source_tree.code)
        for name, codemod_kls in codemods_to_run.items():
            logging.info("Running codemod %s", name)
            command_instance = codemod_kls(CodemodContext())
            output_tree = command_instance.transform_module(source_tree)
            changed_file = not output_tree.deep_equals(source_tree)

            if changed_file:
                print(f"*** CHANGED with {name}:")
                print(output_tree.code)

                if argv.dry_run:
                    logging.info("Dry run, not changing files")
                else:
                    print(f"Updated file {file_path}")
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(output_tree.code)

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
