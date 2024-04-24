import argparse
import json
import sys

from codemodder import __version__
from codemodder.code_directory import DEFAULT_EXCLUDED_PATHS
from codemodder.logging import OutputFormat, logger
from codemodder.registry import CodemodRegistry


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        """If there is an argument parsing error, print the `--help` message,
        log the error, and exit with status code `3`."""
        self.print_help(sys.stderr)
        logger.error("CLI error: %s", message)
        sys.exit(3)


def build_list_action(codemod_registry: CodemodRegistry):
    class ListAction(argparse.Action):
        """ """

        def _print_codemods(self):
            for codemod_id in sorted(codemod_registry.ids):
                print(codemod_id)

        def __call__(self, parser, *args, **kwargs):
            """
            Print codemod(s) metadata in the following format:

            pixee:python/secure-random
            pixee:python/url-sandbox
            ...

            and exit gracefully.
            """
            self._print_codemods()
            parser.exit()

    return ListAction


def build_describe_action(codemod_registry: CodemodRegistry):
    class DescribeAction(argparse.Action):
        def _print_codemods(self, args: argparse.Namespace):
            # TODO: this doesn't currently honor the include/exclude args
            # This is because of the way arguments are parsed: at the time this
            # action is called, the codemod arguments haven't necessarily been
            # parsed yet. Making this work will require a fairly significant
            # refactor of the argument parsing.
            results = codemod_registry.describe_codemods(
                args.codemod_include, args.codemod_exclude
            )
            print(json.dumps({"results": results}, indent=2))

        def __call__(self, parser, *args, **kwargs):
            parsed_args: argparse.Namespace = args[0]
            self._print_codemods(parsed_args)
            parser.exit()

    return DescribeAction


class CsvListAction(argparse.Action):
    """
    argparse Action to convert "a,b,c" into ["a", "b", "c"]
    """

    def __call__(self, parser, namespace, values, option_string=None):
        # Conversion to dict removes duplicates while preserving order
        items = list(dict.fromkeys(values.split(",")).keys())
        setattr(namespace, self.dest, items)


def parse_args(argv, codemod_registry: CodemodRegistry):
    """
    Parse CLI arguments according to:
    https://www.notion.so/pixee/Codemodder-CLI-Arguments
    """
    parser = ArgumentParser(description="Run codemods and change code.")

    parser.add_argument("directory", type=str, help="path to find files")
    parser.add_argument(
        "--output",
        type=str,
        help="name of output file to produce",
    )

    codemod_args_group = parser.add_mutually_exclusive_group()
    codemod_args_group.add_argument(
        "--codemod-exclude",
        action=CsvListAction,
        help="Comma-separated set of codemod ID(s) to exclude",
    )
    codemod_args_group.add_argument(
        "--codemod-include",
        action=CsvListAction,
        help="Comma-separated set of codemod ID(s) to include",
    )

    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument(
        "--list",
        action=build_list_action(codemod_registry),
        nargs=0,
        help="Print codemod names to stdout and exit",
    )
    parser.add_argument(
        "--describe",
        action=build_describe_action(codemod_registry),
        nargs=0,
        help="Print detailed codemod metadata to stdout exit",
    )
    parser.add_argument(
        "--output-format",
        type=str,
        help="the format for the data output file",
        default="codetf",
        choices=["codetf", "diff"],
    )
    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        help="do everything except make changes to files",
    )
    parser.add_argument(
        "--verbose",
        action=argparse.BooleanOptionalAction,
        help="print more to stdout",
    )
    parser.add_argument(
        "--log-format",
        type=OutputFormat,
        default=OutputFormat.HUMAN,
        choices=[OutputFormat.HUMAN, OutputFormat.JSON],
        help="the format for the log output",
    )
    parser.add_argument(
        "--project-name",
        help="optional descriptive name for the project used in log output",
    )
    parser.add_argument(
        "--path-exclude",
        action=CsvListAction,
        default=DEFAULT_EXCLUDED_PATHS,
        help="Comma-separated set of UNIX glob patterns to exclude",
    )
    parser.add_argument(
        "--path-include",
        action=CsvListAction,
        default=[],
        help="Comma-separated set of UNIX glob patterns to include",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=1,
        help="maximum number of workers (threads) to use for processing files in parallel",
    )

    parser.add_argument(
        "--sarif",
        action=CsvListAction,
        help="Comma-separated set of path(s) to SARIF file(s) to feed to the codemods",
    )
    parser.add_argument(
        "--sonar-issues-json",
        action=CsvListAction,
        help="Comma-separated set of path(s) to Sonar issues JSON file(s) to feed to the codemods",
    )
    parser.add_argument(
        "--sonar-hotspots-json",
        action=CsvListAction,
        help="Comma-separated set of path(s) to Sonar hotspots JSON file(s) to feed to the codemods",
    )
    parser.add_argument(
        "--defectdojo-findings-json",
        action=CsvListAction,
        help="Comma-separated set of path(s) to DefectDojo's v2 Findings JSON file(s) to feed to the codemods",
    )
    parser.add_argument(
        "--contrast-vulnerabilities-xml",
        action=CsvListAction,
        help="Comma-separated set of path(s) to Contrast Security's vulnerabilities XML file(s) to feed to the codemods",
    )
    return parser.parse_args(argv)
