import mock
import pytest
from codemodder.__main__ import run
from codemodder.semgrep import run as semgrep_run
from codemodder.cli import parse_args
from .conftest import CODEMOD_NAMES


class TestRun:
    @mock.patch("libcst.parse_module")
    @mock.patch("codemodder.__main__.logger.warning")
    def test_no_files_matched(self, warning_log, mock_parse):
        args = [
            "tests/samples/",
            "--output",
            "here.txt",
            "--codemod-include=url-sandbox",
            "--path-exclude",
            "*py",
        ]
        res = run(parse_args(args), args)
        assert res == 0

        warning_log.assert_called()
        assert warning_log.call_args_list[0][0][0] == "No files matched."

        mock_parse.assert_not_called()

    @mock.patch("libcst.parse_module", side_effect=Exception)
    @mock.patch("codemodder.__main__.report_default")
    def test_cst_parsing_fails(self, mock_reporting, mock_parse):
        args = [
            "tests/samples/",
            "--output",
            "here.txt",
        ]

        res = run(parse_args(args), args)

        assert res == 0
        mock_parse.assert_called()

        # We still report for now even if parsing failed
        mock_reporting.assert_called_once()
        args_to_reporting = mock_reporting.call_args_list[0][0]
        assert len(args_to_reporting) == 4
        _, _, _, results_by_codemod = args_to_reporting
        assert results_by_codemod == []

    @mock.patch("codemodder.__main__.logger.info")
    @mock.patch("codemodder.__main__.update_code")
    @mock.patch("codemodder.__main__.semgrep_run", side_effect=semgrep_run)
    def test_dry_run(self, _, mock_update_code, info_log):
        args = [
            "tests/samples/",
            "--output",
            "here.txt",
            "--dry-run",
        ]

        res = run(parse_args(args), args)
        assert res == 0

        info_log.assert_called()

        logged_msgs = [
            info_log.call_args_list[x][0][0]
            for x in range(len(info_log.call_args_list))
        ]
        assert "Dry run, not changing files" in logged_msgs

        mock_update_code.assert_not_called()

    @pytest.mark.parametrize("dry_run", [True, False])
    @mock.patch("codemodder.__main__.report_default")
    def test_reporting(self, mock_reporting, dry_run):
        args = [
            "tests/samples/",
            "--output",
            "here.txt",
        ]
        if dry_run:
            args += ["--dry-run"]

        res = run(parse_args(args), args)
        assert res == 0

        mock_reporting.assert_called_once()
        args_to_reporting = mock_reporting.call_args_list[0][0]
        assert len(args_to_reporting) == 4
        _, _, _, results_by_codemod = args_to_reporting
        # assert len(results_by_codemod) == 2

        for codemod_results in results_by_codemod:
            assert len(codemod_results["changeset"]) > 0

    @mock.patch("codemodder.__main__.semgrep_run")
    def test_no_codemods_to_run(self, mock_semgrep_run):
        names = ",".join(CODEMOD_NAMES)
        args = [
            "tests/samples/",
            "--output",
            "here.txt",
            f"--codemod-exclude={names}",
        ]

        exit_code = run(parse_args(args), args)
        assert exit_code == 0
        mock_semgrep_run.assert_not_called()


class TestExitCode:
    def test_success_0(self):
        args = [
            "tests/samples/",
            "--output",
            "here.txt",
            "--codemod-include=url-sandbox",
            "--path-exclude",
            "*request.py",
        ]

        exit_code = run(parse_args(args), args)
        assert exit_code == 0

    def test_bad_project_dir_1(self):
        args = [
            "bad/path/",
            "--output",
            "here.txt",
            "--codemod-include=url-sandbox",
        ]

        exit_code = run(parse_args(args), args)
        assert exit_code == 1

    def test_conflicting_include_exclude(self):
        args = [
            "tests/samples/",
            "--output",
            "here.txt",
            "--codemod-exclude",
            "secure-random",
            "--codemod-include",
            "secure-random",
        ]
        with pytest.raises(SystemExit) as err:
            run(parse_args(args), args)
        assert err.value.args[0] == 3

    def test_bad_codemod_name(self):
        bad_codemod = "doesntexist"
        args = [
            "tests/samples/",
            "--output",
            "here.txt",
            f"--codemod-include={bad_codemod}",
        ]
        with pytest.raises(SystemExit) as err:
            run(parse_args(args), args)
        assert err.value.args[0] == 3
