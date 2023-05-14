import mock
import pytest
from codemodder.cli import parse_args
from codemodder import __VERSION__
from codemodder.codemods import CODEMODS

NAMES = tuple(CODEMODS.keys())


class TestParseArgs:
    def test_no_args(self):
        with pytest.raises(SystemExit) as err:
            parse_args([])
        assert "CLI error: the following arguments are required:" in err.value.args[0]

    @pytest.mark.parametrize(
        "cli_args",
        [
            ["--help"],
            [
                "tests/samples/",
                "--output",
                "here.txt",
                "--codemod=url_sandbox",
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
                "--codemod=url_sandbox",
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
                "--codemod=url_sandbox",
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
            assert print_call[0][0].endswith(NAMES)

        assert err.value.args[0] == 0

    def test_bad_output_format(self):
        with pytest.raises(SystemExit) as err:
            parse_args(
                [
                    "tests/samples/",
                    "--output",
                    "here.txt",
                    "--codemod=url_sandbox",
                    "--output-format",
                    "hello",
                ]
            )
        assert (
            err.value.args[0]
            == "CLI error: argument --output-format: invalid choice: 'hello' (choose from 'codetf', 'diff')"
        )

    def test_path_exclude(self):
        # should split it into list
        parse_args(
            [
                "tests/samples/",
                "--output",
                "here.txt",
                "--codemod=url-sandbox",
                "--path-exclude",
                "*request",
            ]
        )
