import mock
import pytest
from codemodder.cli import parse_args
from codemodder import __VERSION__

# from .conftest import CODEMOD_NAMES
from codemodder.codemods import DEFAULT_CODEMODS

CODEMOD_FULL_NAMES = tuple(codemod.full_name() for codemod in DEFAULT_CODEMODS)


class TestParseArgs:
    @mock.patch("codemodder.cli.logger.error")
    def test_no_args(self, error_logger):
        with pytest.raises(SystemExit) as err:
            parse_args([])
        assert err.value.args[0] == 3
        error_logger.assert_called()
        assert error_logger.call_args_list[0][0] == (
            "CLI error: %s",
            "the following arguments are required: directory, --output",
        )

    @pytest.mark.parametrize(
        "cli_args",
        [
            ["--help"],
            [
                "tests/samples/",
                "--output",
                "here.txt",
                "--codemod-include=url-sandbox",
                "--help",
            ],
        ],
    )
    @mock.patch("argparse.ArgumentParser.print_help")
    def test_help_is_printed(self, mock_print_help, cli_args):
        with pytest.raises(SystemExit) as err:
            parse_args(cli_args)

        mock_print_help.assert_called()
        assert err.value.args[0] == 0

    @pytest.mark.parametrize(
        "cli_args",
        [
            ["--version"],
            [
                "tests/samples/",
                "--output",
                "here.txt",
                "--codemod-include=url-sandbox",
                "--version",
            ],
        ],
    )
    @mock.patch("argparse.ArgumentParser._print_message")
    def test_version_is_printed(self, mock_print_msg, cli_args):
        with pytest.raises(SystemExit) as err:
            parse_args(cli_args)

        assert mock_print_msg.call_args_list[0][0][0].strip() == __VERSION__
        assert err.value.args[0] == 0

    @pytest.mark.parametrize(
        "cli_args",
        [
            ["--list"],
            [
                "tests/samples/",
                "--output",
                "here.txt",
                "--list",
            ],
        ],
    )
    @mock.patch("builtins.print")
    def test_list_prints_codemod_metadata(self, mock_print, cli_args):
        with pytest.raises(SystemExit) as err:
            parse_args(cli_args)

        assert len(mock_print.call_args_list) == len(CODEMOD_FULL_NAMES)

        printed_names = [call[0][0] for call in mock_print.call_args_list]
        assert sorted(CODEMOD_FULL_NAMES) == sorted(printed_names)

        assert err.value.args[0] == 0

    @mock.patch("codemodder.cli.logger.error")
    def test_bad_output_format(self, error_logger):
        with pytest.raises(SystemExit) as err:
            parse_args(
                [
                    "tests/samples/",
                    "--output",
                    "here.txt",
                    "--output-format",
                    "hello",
                ]
            )
        assert err.value.args[0] == 3
        error_logger.assert_called()
        assert error_logger.call_args_list[0][0] == (
            "CLI error: %s",
            "argument --output-format: invalid choice: 'hello' (choose from 'codetf', 'diff')",
        )

    @mock.patch("codemodder.cli.logger.error")
    def test_bad_option(self, error_logger):
        with pytest.raises(SystemExit) as err:
            parse_args(
                [
                    "tests/samples/",
                    "--output",
                    "here.txt",
                    "--codemod=url-sandbox",
                    "--path-exclude",
                    "*request.py",
                ]
            )
        assert err.value.args[0] == 3
        error_logger.assert_called()
        assert error_logger.call_args_list[0][0] == (
            "CLI error: %s",
            "ambiguous option: --codemod=url-sandbox could match --codemod-exclude, --codemod-include",
        )

    @pytest.mark.parametrize("codemod", ["secure-random", "pixee:python/secure-random"])
    def test_codemod_name_or_id(self, codemod):
        parse_args(
            [
                "tests/samples/",
                "--output",
                "here.txt",
                f"--codemod-include={codemod}",
            ]
        )
