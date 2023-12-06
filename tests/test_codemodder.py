import mock
import pytest

import libcst as cst

from codemodder.codemodder import run, find_semgrep_results
from codemodder.diff import create_diff_from_tree
from codemodder.semgrep import run as semgrep_run
from codemodder.registry import load_registered_codemods
from codemodder.result import ResultSet


@pytest.fixture(autouse=True, scope="module")
def disable_write_report():
    """Override fixture from conftest.py"""


class TestRun:
    @mock.patch("libcst.parse_module")
    def test_no_files_matched(self, mock_parse, tmpdir):
        codetf = tmpdir / "result.codetf"
        assert not codetf.exists()

        args = [
            "tests/samples/",
            "--output",
            str(codetf),
            "--codemod-include=url-sandbox",
            "--path-exclude",
            "*py",
        ]
        res = run(args)
        assert res == 0

        mock_parse.assert_not_called()
        assert codetf.exists()

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
    def test_dry_run(self, _, mock_update_code, tmpdir):
        codetf = tmpdir / "result.codetf"
        args = [
            "tests/samples/",
            "--output",
            str(codetf),
            "--dry-run",
            # Make this test faster by restricting the number of codemods
            "--codemod-include=url-sandbox",
        ]

        assert not codetf.exists()

        res = run(args)
        assert res == 0
        assert codetf.exists()

        mock_update_code.assert_not_called()

    @pytest.mark.parametrize("dry_run", [True, False])
    @mock.patch("codemodder.codemodder.report_default")
    def test_reporting(self, mock_reporting, dry_run):
        args = [
            "tests/samples/",
            "--output",
            "here.txt",
            # Make this test faster by restricting the number of codemods
            "--codemod-include=use-generator,use-defusedxml,use-walrus-if",
        ]
        if dry_run:
            args += ["--dry-run"]

        res = run(args)
        assert res == 0

        mock_reporting.assert_called_once()
        args_to_reporting = mock_reporting.call_args_list[0][0]
        assert len(args_to_reporting) == 4
        _, _, _, results_by_codemod = args_to_reporting

        assert len(results_by_codemod) == 3

    @mock.patch("codemodder.codemods.base_codemod.semgrep_run")
    def test_no_codemods_to_run(self, mock_semgrep_run, tmpdir):
        codetf = tmpdir / "result.codetf"
        assert not codetf.exists()

        registry = load_registered_codemods()
        names = ",".join(registry.names)
        args = [
            "tests/samples/",
            "--output",
            str(codetf),
            f"--codemod-exclude={names}",
        ]

        exit_code = run(args)
        assert exit_code == 0
        mock_semgrep_run.assert_not_called()
        assert codetf.exists()

    @pytest.mark.parametrize("codemod", ["secure-random", "pixee:python/secure-random"])
    @mock.patch("codemodder.context.CodemodExecutionContext.compile_results")
    @mock.patch("codemodder.codemodder.report_default")
    def test_run_codemod_name_or_id(
        self, report_default, mock_compile_results, codemod
    ):
        del report_default
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
    @mock.patch("codemodder.codemodder.report_default")
    def test_success_0(self, mock_report):
        del mock_report
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

    @mock.patch("codemodder.codemodder.report_default")
    def test_bad_project_dir_1(self, mock_report):
        del mock_report
        args = [
            "bad/path/",
            "--output",
            "here.txt",
            "--codemod-include=url-sandbox",
        ]

        exit_code = run(args)
        assert exit_code == 1

    @mock.patch("codemodder.codemodder.report_default")
    def test_conflicting_include_exclude(self, mock_report):
        del mock_report
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

    @mock.patch("codemodder.codemodder.report_default")
    def test_bad_codemod_name(self, mock_report):
        del mock_report
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

    def test_find_semgrep_results(self, mocker):
        run_semgrep = mocker.patch("codemodder.codemodder.run_semgrep")
        codemods = load_registered_codemods()
        find_semgrep_results(mocker.MagicMock(), codemods.codemods)
        assert run_semgrep.call_count == 1

    def test_find_semgrep_results_no_yaml(self, mocker):
        run_semgrep = mocker.patch("codemodder.codemodder.run_semgrep")
        codemods = load_registered_codemods().match_codemods(
            codemod_include=["use-defusedxml"]
        )
        result = find_semgrep_results(mocker.MagicMock(), codemods)
        assert result == ResultSet()
        assert run_semgrep.call_count == 0

    def test_diff_newline_edge_case(self):
        source = """
SECRET_COOKIE_KEY = "PYGOAT"
CSRF_TRUSTED_ORIGINS = ["http://127.0.0.1:8000","http://0.0.0.0:8000","http://172.16.189.10"]"""  # no newline here

        result = """
SECRET_COOKIE_KEY = "PYGOAT"
CSRF_TRUSTED_ORIGINS = ["http://127.0.0.1:8000","http://0.0.0.0:8000","http://172.16.189.10"]
SESSION_COOKIE_SECURE = True"""

        source_tree = cst.parse_module(source)
        result_tree = cst.parse_module(result)

        diff = create_diff_from_tree(source_tree, result_tree)
        assert (
            diff
            == """\
--- 
+++ 
@@ -1,3 +1,4 @@
 
 SECRET_COOKIE_KEY = "PYGOAT"
-CSRF_TRUSTED_ORIGINS = ["http://127.0.0.1:8000","http://0.0.0.0:8000","http://172.16.189.10"]
+CSRF_TRUSTED_ORIGINS = ["http://127.0.0.1:8000","http://0.0.0.0:8000","http://172.16.189.10"]
+SESSION_COOKIE_SECURE = True"""
        )
