import mock
import pytest
from codemodder.codemodder import run
from codemodder.semgrep import run as semgrep_run
from codemodder.registry import load_registered_codemods


class TestRun:
    @mock.patch("libcst.parse_module")
    @mock.patch("codemodder.codemodder.logger.error")
    def test_no_files_matched(self, error_log, mock_parse):
        args = [
            "tests/samples/",
            "--output",
            "here.txt",
            "--codemod-include=url-sandbox",
            "--path-exclude",
            "*py",
        ]
        res = run(args)
        assert res == 0

        error_log.assert_called()
        assert error_log.call_args_list[0][0][0] == "no files matched."

        mock_parse.assert_not_called()

    @mock.patch("libcst.parse_module", side_effect=Exception)
    @mock.patch("codemodder.codemodder.report_default")
    def test_cst_parsing_fails(self, mock_reporting, mock_parse):
        args = [
            "tests/samples/",
            "--output",
            "here.txt",
            "--codemod-include",
            "requests-verify",
            "--path-include",
            "*request.py",
        ]

        res = run(args)

        assert res == 0
        mock_parse.assert_called()

        mock_reporting.assert_called_once()
        args_to_reporting = mock_reporting.call_args_list[0][0]
        assert len(args_to_reporting) == 4
        _, _, _, results_by_codemod = args_to_reporting
        assert results_by_codemod != []

        requests_report = results_by_codemod[0]
        assert requests_report["changeset"] == []
        assert len(requests_report["failedFiles"]) == 2
        assert sorted(requests_report["failedFiles"]) == [
            "tests/samples/make_request.py",
            "tests/samples/unverified_request.py",
        ]

    @mock.patch("codemodder.codemodder.update_code")
    @mock.patch("codemodder.codemods.base_codemod.semgrep_run", side_effect=semgrep_run)
    def test_dry_run(self, _, mock_update_code):
        args = [
            "tests/samples/",
            "--output",
            "here.txt",
            "--dry-run",
        ]

        res = run(args)
        assert res == 0

        mock_update_code.assert_not_called()

    @pytest.mark.parametrize("dry_run", [True, False])
    @mock.patch("codemodder.codemodder.report_default")
    def test_reporting(self, mock_reporting, dry_run):
        args = [
            "tests/samples/",
            "--output",
            "here.txt",
        ]
        if dry_run:
            args += ["--dry-run"]

        res = run(args)
        assert res == 0

        mock_reporting.assert_called_once()
        args_to_reporting = mock_reporting.call_args_list[0][0]
        assert len(args_to_reporting) == 4
        _, _, _, results_by_codemod = args_to_reporting

        registry = load_registered_codemods()
        assert len(results_by_codemod) == len(registry.codemods)

    @mock.patch("codemodder.codemods.base_codemod.semgrep_run")
    def test_no_codemods_to_run(self, mock_semgrep_run):
        registry = load_registered_codemods()
        names = ",".join(registry.names)
        args = [
            "tests/samples/",
            "--output",
            "here.txt",
            f"--codemod-exclude={names}",
        ]

        exit_code = run(args)
        assert exit_code == 0
        mock_semgrep_run.assert_not_called()

    @pytest.mark.parametrize("codemod", ["secure-random", "pixee:python/secure-random"])
    @mock.patch("codemodder.context.CodemodExecutionContext.compile_results")
    def test_run_codemod_name_or_id(self, mock_compile_results, codemod):
        args = [
            "tests/samples/",
            "--output",
            "here.txt",
            f"--codemod-include={codemod}",
        ]

        exit_code = run(args)
        assert exit_code == 0
        mock_compile_results.assert_called()


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

        exit_code = run(args)
        assert exit_code == 0

    def test_bad_project_dir_1(self):
        args = [
            "bad/path/",
            "--output",
            "here.txt",
            "--codemod-include=url-sandbox",
        ]

        exit_code = run(args)
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
            run(args)
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
            run(args)
        assert err.value.args[0] == 3
