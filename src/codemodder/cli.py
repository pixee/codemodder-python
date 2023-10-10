import argparse
import sys

from codemodder import __VERSION__
from codemodder.logging import OutputFormat, logger


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        """If there is an argument parsing error, print the `--help` message,
        log the error, and exit with status code `3`."""
        self.print_help(sys.stderr)
        logger.error("CLI error: %s", message)
        sys.exit(3)


def build_list_action(codemod_registry):
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


class CsvListAction(argparse.Action):
    """
    argparse Action to convert "a,b,c" into ["a", "b", "c"]
    """

    def __call__(self, parser, namespace, values: str, option_string=None):
        # Conversion to dict removes duplicates while preserving order
        items = list(dict.fromkeys(values.split(",")).keys())
        self.validate_items(items)
        setattr(namespace, self.dest, items)

    def validate_items(self, items):
        """Basic Action does not validate the items"""


def build_codemod_validator(codemod_registry):
    names = codemod_registry.names
    ids = codemod_registry.ids

    class ValidatedCodmods(CsvListAction):
        """
        argparse Action to convert "codemod1,codemod2,codemod3" into a list
        representation and validate against existing codemods
        """

        def validate_items(self, items):
            potential_names = ids + names
            unrecognized_codemods = [
                name for name in items if name not in potential_names
            ]

            if unrecognized_codemods:
                args = {
                    "values": unrecognized_codemods,
                    "choices": ", ".join(map(repr, names)),
                }
                msg = "invalid choice(s): %(values)r (choose from %(choices)s)"
                raise argparse.ArgumentError(self, msg % args)

    return ValidatedCodmods


def parse_args(argv, codemod_registry):
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
        default="stdout",
        required=True,
    )

    codemod_validator = build_codemod_validator(codemod_registry)

    codemod_args_group = parser.add_mutually_exclusive_group()
    codemod_args_group.add_argument(
        "--codemod-exclude",
        action=codemod_validator,
        help="Comma-separated set of codemod ID(s) to exclude",
    )
    codemod_args_group.add_argument(
        "--codemod-include",
        action=codemod_validator,
        help="Comma-separated set of codemod ID(s) to include",
    )

    parser.add_argument("--version", action="version", version=__VERSION__)
    parser.add_argument(
        "--list",
        action=build_list_action(codemod_registry),
        nargs=0,
        help="Print codemod(s) metadata",
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
        choices=[str(x).split(".")[-1].lower() for x in list(OutputFormat)],
        help="the format for the log output",
    )
    parser.add_argument(
        "--path-exclude",
        action=CsvListAction,
        default="",
        help="Comma-separated set of UNIX glob patterns to exclude",
    )
    parser.add_argument(
        "--path-include",
        action=CsvListAction,
        default="**/*.py",
        help="Comma-separated set of UNIX glob patterns to include",
    )

    # At this time we don't do anything with the sarif arg.
    parser.add_argument(
        "--sarif",
        action=CsvListAction,
        help="Comma-separated set of path(s) to SARIF file(s) to feed to the codemods",
    )
    return parser.parse_args(argv)
