import mock
from codemodder.__main__ import run
from codemodder.cli import parse_args


class TestRun:
    @mock.patch("codemodder.__main__.logging.warning")
    def test_no_files_matched(self, warning_log):
        res = run(
            parse_args(
                [
                    "tests/samples/",
                    "--output",
                    "here.txt",
                    "--codemod-include=url-sandbox",
                    "--path-exclude",
                    "*py",
                ]
            )
        )
        assert res is None

        warning_log.assert_called()
        assert warning_log.call_args_list[0][0][0] == "No files matched."

    @mock.patch("libcst.parse_module", side_effect=Exception)
    def test_cst_parsing_fails(self, mock_parse):
        res = run(
            parse_args(
                [
                    "tests/samples/",
                    "--output",
                    "here.txt",
                ]
            )
        )
        assert res is 0
        mock_parse.assert_called()

    @mock.patch("codemodder.__main__.logging.info")
    def test_dry_run(self, info_log):
        res = run(
            parse_args(
                [
                    "tests/samples/",
                    "--output",
                    "here.txt",
                    "--dry-run",
                ]
            )
        )
        assert res is 0

        info_log.assert_called()
        assert info_log.call_args_list[-1][0][0] == "Dry run, not changing files"


class TestExitCode:
    def test_success_0(self):
        run(
            parse_args(
                [
                    "tests/samples/",
                    "--output",
                    "here.txt",
                    "--codemod-include=url-sandbox",
                    "--path-exclude",
                    "*request.py",
                ]
            )
        )

    def test_bad_project_dir_1(self):
        exit_code = run(
            parse_args(
                [
                    "bad/path/",
                    "--output",
                    "here.txt",
                    "--codemod-include=url-sandbox",
                ]
            )
        )
        assert exit_code == 1
