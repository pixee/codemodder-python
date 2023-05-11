import mock
import pytest
from src.main import parse_args
from src import __VERSION__


class TestParseArgs:
    def test_no_args(self):
        with pytest.raises(SystemExit) as err:
            parse_args([])
        assert (
            err.value.args[0]
            == "the following arguments are required: directory, output"
        )

    @pytest.mark.parametrize(
        "cli_args",
        [["--help"], ["tests/samples/", "here.txt", "--codemod=url_sandbox", "--help"]],
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
            ["tests/samples/", "here.txt", "--codemod=url_sandbox", "--version"],
        ],
    )
    @mock.patch("argparse.ArgumentParser._print_message")
    def test_version_is_printed(self, mock_print_msg, cli_args):
        with pytest.raises(SystemExit) as err:
            parse_args(cli_args)

        assert mock_print_msg.call_args_list[0][0][0].strip() == __VERSION__
        assert err.value.args[0] == 0
