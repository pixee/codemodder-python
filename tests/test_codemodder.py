import libcst as cst
import mock
import pytest

from codemodder.codemodder import find_semgrep_results, run
from codemodder.diff import create_diff_from_tree
from codemodder.registry import load_registered_codemods
from codemodder.result import ResultSet
from codemodder.semgrep import run as semgrep_run


@pytest.fixture(autouse=True, scope="module")
def disable_write_report():
    """Override fixture from conftest.py"""


@pytest.fixture(autouse=True)
def disable_codemod_apply(mocker, request):
    """
    The tests in this module are like integration tests in that they  often
    run all of codemodder but we most often don't need to actually apply codemods.
    """
    # Skip mocking only for specific tests that need to apply codemods.
    if request.function.__name__ == "test_cst_parsing_fails":
        return
    mocker.patch("codemodder.codemods.base_codemod.BaseCodemod.apply")


class TestRun:
    @mock.patch("libcst.parse_module")
    def test_no_files_matched(self, mock_parse, tmpdir):
        codetf = tmpdir / "result.codetf"
        code_dir = tmpdir.mkdir("code")
        code_dir.join("code.py").write("# anything")
        assert not codetf.exists()

        args = [
            str(code_dir),
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
    @mock.patch("codemodder.codetf.CodeTF.build")
    def test_cst_parsing_fails(self, build_report, mock_parse, tmpdir):
        code_dir = tmpdir.mkdir("code")
        code_file = code_dir.join("test_request.py")
        code_file.write("# anything")

        args = [
            str(code_dir),
            "--output",
            str(tmpdir / "result.codetf"),
            "--codemod-include",
            "fix-assert-tuple",
            "--path-include",
            "*request.py",
        ]

        res = run(args)

        assert res == 0
        mock_parse.assert_called()

        build_report.assert_called_once()
        args_to_reporting = build_report.call_args_list[0][0]
        assert len(args_to_reporting) == 4
        _, _, _, results_by_codemod = args_to_reporting
        assert results_by_codemod != []

        requests_report = results_by_codemod[0]
        assert requests_report.changeset == []
        assert len(requests_report.failedFiles) == 1
        assert sorted(requests_report.failedFiles) == [
            str(code_file),
        ]

        build_report.return_value.write_report.assert_called_once()

    @mock.patch("codemodder.codemods.libcst_transformer.update_code")
    @mock.patch("codemodder.codemods.semgrep.semgrep_run", side_effect=semgrep_run)
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
    @mock.patch("codemodder.codetf.CodeTF.build")
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

        mock_reporting.return_value.write_report.assert_called_once()

    @pytest.mark.parametrize("codemod", ["secure-random", "pixee:python/secure-random"])
    @mock.patch("codemodder.context.CodemodExecutionContext.compile_results")
    @mock.patch("codemodder.codetf.CodeTF.write_report")
    def test_run_codemod_name_or_id(self, write_report, mock_compile_results, codemod):
        del write_report
        args = [
            "tests/samples/",
            "--output",
            "here.txt",
            f"--codemod-include={codemod}",
        ]

        exit_code = run(args)
        assert exit_code == 0
        # todo: if no codemods run do we still compile results?
        mock_compile_results.assert_called()


class TestCodemodIncludeExclude:

    @mock.patch("codemodder.registry.logger.warning")
    @mock.patch("codemodder.codemodder.logger.info")
    @mock.patch("codemodder.codetf.CodeTF.write_report")
    def test_codemod_include_no_match(self, write_report, info_logger, warning_logger):
        bad_codemod = "doesntexist"
        args = [
            "tests/samples/",
            "--output",
            "here.txt",
            f"--codemod-include={bad_codemod}",
        ]
        run(args)
        write_report.assert_called_once()

        assert any("no codemods to run" in x[0][0] for x in info_logger.call_args_list)
        assert any(x[0] == ("scanned: %s files", 0) for x in info_logger.call_args_list)

        assert any(
            f"Requested codemod to include'{bad_codemod}' does not exist." in x[0][0]
            for x in warning_logger.call_args_list
        )

    @mock.patch("codemodder.registry.logger.warning")
    @mock.patch("codemodder.codemodder.logger.info")
    @mock.patch("codemodder.codetf.CodeTF.write_report")
    def test_codemod_include_some_match(
        self, write_report, info_logger, warning_logger
    ):
        bad_codemod = "doesntexist"
        good_codemod = "secure-random"
        args = [
            "tests/samples/",
            "--output",
            "here.txt",
            f"--codemod-include={bad_codemod},{good_codemod}",
        ]
        run(args)
        write_report.assert_called_once()
        assert any("running codemod %s" in x[0][0] for x in info_logger.call_args_list)
        assert any(
            f"Requested codemod to include'{bad_codemod}' does not exist." in x[0][0]
            for x in warning_logger.call_args_list
        )

    @mock.patch("codemodder.registry.logger.warning")
    @mock.patch("codemodder.codemodder.logger.info")
    @mock.patch("codemodder.codetf.CodeTF.write_report")
    def test_codemod_exclude_some_match(
        self, write_report, info_logger, warning_logger
    ):
        bad_codemod = "doesntexist"
        good_codemod = "secure-random"
        args = [
            "tests/samples/",
            "--output",
            "here.txt",
            f"--codemod-exclude={bad_codemod},{good_codemod}",
        ]
        run(args)
        write_report.assert_called_once()
        codemods_that_ran = [
            x[0][1]
            for x in info_logger.call_args_list
            if x[0][0] == "running codemod %s"
        ]

        assert f"pixee:python/{good_codemod}" not in codemods_that_ran
        assert any("running codemod %s" in x[0][0] for x in info_logger.call_args_list)
        assert any(
            f"Requested codemod to exclude'{bad_codemod}' does not exist." in x[0][0]
            for x in warning_logger.call_args_list
        )

    @mock.patch("codemodder.registry.logger.warning")
    @mock.patch("codemodder.codemodder.logger.info")
    @mock.patch("codemodder.codetf.CodeTF.write_report")
    @mock.patch("codemodder.codemods.base_codemod.BaseCodemod.apply")
    def test_codemod_exclude_no_match(
        self, apply, write_report, info_logger, warning_logger
    ):
        bad_codemod = "doesntexist"
        args = [
            "tests/samples/",
            "--output",
            "here.txt",
            f"--codemod-exclude={bad_codemod}",
        ]

        run(args)
        write_report.assert_called_once()
        assert any("running codemod %s" in x[0][0] for x in info_logger.call_args_list)
        assert any(
            f"Requested codemod to exclude'{bad_codemod}' does not exist." in x[0][0]
            for x in warning_logger.call_args_list
        )

    @mock.patch("codemodder.codemods.semgrep.semgrep_run")
    def test_exclude_all_registered_codemods(self, mock_semgrep_run, tmpdir):
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


class TestExitCode:
    @mock.patch("codemodder.codetf.CodeTF.write_report")
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

    @mock.patch("codemodder.codetf.CodeTF.write_report")
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

    @mock.patch("codemodder.codetf.CodeTF.write_report")
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
