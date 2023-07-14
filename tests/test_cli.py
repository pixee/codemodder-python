import mock
import pytest
from codemodder.cli import parse_args
from codemodder import __VERSION__
from .conftest import CODEMOD_NAMES


class TestParseArgs:
    @mock.patch("codemodder.cli.logger.error")
    def test_no_args(self, error_logger):
        with pytest.raises(SystemExit) as err:
            parse_args([])
        assert err.value.args[0] == 3
        error_logger.assert_called()
        assert (
            error_logger.call_args_list[0][0][0]
            == "CLI error: the following arguments are required: directory, --output"
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

        for print_call in mock_print.call_args_list:
            assert print_call[0][0].startswith("pixee:python/")
            assert print_call[0][0].endswith(CODEMOD_NAMES)

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
        assert (
            error_logger.call_args_list[0][0][0]
            == "CLI error: argument --output-format: invalid choice: 'hello' (choose from 'codetf', 'diff')"
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
        assert (
            error_logger.call_args_list[0][0][0]
            == "CLI error: ambiguous option: --codemod=url-sandbox could match --codemod-exclude, --codemod-include"
        )
