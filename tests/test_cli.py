import json

import mock
import pytest

from codemodder import __version__
from codemodder.cli import parse_args
from codemodder.registry import DEFAULT_EXCLUDED_CODEMODS, load_registered_codemods
from core_codemods import registry as core_registry


class TestParseArgs:
    @classmethod
    def setup_class(cls):
        cls.registry = load_registered_codemods()

    def test_no_args(self, mocker, caplog):
        with pytest.raises(SystemExit) as err:
            parse_args([], mocker.MagicMock())
        assert err.value.args[0] == 3
        assert (
            "CLI error: the following arguments are required: directory"
            in caplog.messages
        )

    @pytest.mark.parametrize(
        "cli_args",
        [
            ["--help"],
            [
                "some/path",
                "--output",
                "here.txt",
                "--codemod-include=pixee:python/url-sandbox",
                "--help",
            ],
        ],
    )
    @mock.patch("argparse.ArgumentParser.print_help")
    def test_help_is_printed(self, mock_print_help, cli_args):
        with pytest.raises(SystemExit) as err:
            parse_args(cli_args, self.registry)

        mock_print_help.assert_called()
        assert err.value.args[0] == 0

    @pytest.mark.parametrize(
        "cli_args",
        [
            ["--version"],
            [
                "some/path",
                "--output",
                "here.txt",
                "--codemod-include=pixee:python/url-sandbox",
                "--version",
            ],
        ],
    )
    @mock.patch("argparse.ArgumentParser._print_message")
    def test_version_is_printed(self, mock_print_msg, cli_args):
        with pytest.raises(SystemExit) as err:
            parse_args(cli_args, self.registry)

        assert mock_print_msg.call_args_list[0][0][0].strip() == __version__
        assert err.value.args[0] == 0

    @pytest.mark.parametrize(
        "cli_args",
        [
            ["--list"],
            [
                "some/path",
                "--output",
                "here.txt",
                "--list",
            ],
        ],
    )
    @mock.patch("builtins.print")
    def test_list_prints_codemod_metadata(self, mock_print, cli_args):
        with pytest.raises(SystemExit) as err:
            parse_args(cli_args, self.registry)

        assert len(mock_print.call_args_list) == len(self.registry.codemods)

        printed_names = [call[0][0] for call in mock_print.call_args_list]
        assert sorted(self.registry.ids) == sorted(printed_names)

        assert err.value.args[0] == 0

    @mock.patch("builtins.print")
    def test_describe_prints_codemod_metadata(self, mock_print):
        with pytest.raises(SystemExit) as err:
            parse_args(
                ["--describe"],
                self.registry,
            )

        assert err.value.args[0] == 0
        assert mock_print.call_count == 1

        results = json.loads(mock_print.call_args_list[0][0][0])
        assert len(results["results"]) == len(core_registry.codemods) - len(
            DEFAULT_EXCLUDED_CODEMODS
        )

    def test_bad_output_format(self, caplog):
        with pytest.raises(SystemExit) as err:
            parse_args(
                [
                    "some/path",
                    "--output",
                    "here.txt",
                    "--output-format",
                    "hello",
                ],
                self.registry,
            )
        assert err.value.args[0] == 3
        assert (
            "CLI error: argument --output-format: invalid choice: 'hello' (choose from 'codetf', 'diff')"
            in caplog.messages
        )

    def test_bad_option(self, caplog):
        with pytest.raises(SystemExit) as err:
            parse_args(
                [
                    "some/path",
                    "--output",
                    "here.txt",
                    "--codemod=url-sandbox",
                    "--path-exclude",
                    "*request.py",
                ],
                self.registry,
            )
        assert err.value.args[0] == 3
        assert (
            "CLI error: ambiguous option: --codemod=url-sandbox could match --codemod-exclude, --codemod-include"
            in caplog.messages
        )

    @pytest.mark.parametrize("codemod", ["secure-random", "pixee:python/secure-random"])
    def test_codemod_name_or_id(self, codemod):
        parse_args(
            [
                "some/path",
                "--output",
                "here.txt",
                f"--codemod-include={codemod}",
            ],
            self.registry,
        )
