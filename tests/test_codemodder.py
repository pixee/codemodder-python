import logging

import libcst as cst
import mock
import pytest

from codemodder import run
from codemodder.codemodder import _run_cli, find_semgrep_results
from codemodder.diff import create_diff_from_tree
from codemodder.llm import TokenUsage
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
    if request.function.__name__ in (
        "test_cst_parsing_fails",
        "test_dry_run",
        "test_run_codemod_name_or_id",
    ):
        return
    mocker.patch(
        "codemodder.codemods.base_codemod.BaseCodemod.apply", return_value=TokenUsage()
    )


@pytest.fixture(scope="function")
def dir_structure(tmp_path_factory):
    code_dir = tmp_path_factory.mktemp("code")
    (code_dir / "test_request.py").write_text(
        """
    from test_sources import untrusted_data
    import requests

    url = untrusted_data()
    requests.get(url)
    var = "hello"
    """
    )
    (code_dir / "test_random.py").write_text(
        """
    import random
    def func(foo=[]):
        return random.random()
    """
    )
    codetf = code_dir / "result.codetf"
    assert not codetf.exists()
    return code_dir, codetf


class TestRunCli:
    @mock.patch("libcst.parse_module")
    def test_no_files_matched(self, mock_parse, dir_structure):
        code_dir, codetf = dir_structure
        args = [
            str(code_dir),
            "--output",
            str(codetf),
            "--codemod-include=pixee:python/url-sandbox",
            "--path-exclude",
            "*py",
        ]
        res = _run_cli(args)
        assert res == 0

        mock_parse.assert_not_called()
        assert codetf.exists()

    def test_skip_symlinks(self, mocker, dir_structure):
        # Override fixture for this specific test case
        mocker.patch("codemodder.codemods.semgrep.semgrep_run", semgrep_run)
        code_dir, codetf = dir_structure
        (code_dir / "symlink.py").symlink_to(code_dir / "test_request.py")
        args = [
            str(code_dir),
            "--output",
            str(codetf),
            "--codemod-include=pixee:python/url-sandbox",
        ]
        res = _run_cli(args)
        assert res == 0

    @mock.patch("libcst.parse_module", side_effect=Exception)
    @mock.patch("codemodder.codetf.CodeTF.build")
    def test_cst_parsing_fails(self, build_report, mock_parse, dir_structure):
        code_dir, codetf = dir_structure
        args = [
            str(code_dir),
            "--output",
            str(codetf),
            "--codemod-include",
            "pixee:python/fix-assert-tuple",
            "--path-include",
            "*request.py",
        ]

        res = _run_cli(args)

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
            str(code_dir / "test_request.py"),
        ]

        build_report.return_value.write_report.assert_called_once()

    def test_dry_run(self, mocker, dir_structure):
        mock_update_code = mocker.patch(
            "codemodder.codemods.libcst_transformer.update_code"
        )
        transform_apply = mocker.patch(
            "codemodder.codemods.libcst_transformer.LibcstTransformerPipeline.apply",
            new_callable=mock.PropertyMock,
        )
        mocker.patch("codemodder.context.CodemodExecutionContext.compile_results")

        code_dir, codetf = dir_structure
        args = [
            str(code_dir),
            "--output",
            str(codetf),
            "--dry-run",
            # Make this test faster by restricting the number of codemods
            "--codemod-include=pixee:python/use-defusedxml",
        ]

        assert not codetf.exists()

        res = _run_cli(args)
        assert res == 0
        assert codetf.exists()
        transform_apply.assert_called()
        mock_update_code.assert_not_called()

    @pytest.mark.parametrize("dry_run", [True, False])
    @mock.patch("codemodder.codetf.CodeTF.build")
    def test_reporting(self, mock_reporting, dry_run, dir_structure):
        code_dir, codetf = dir_structure
        args = [
            str(code_dir),
            "--output",
            str(codetf),
            # Make this test faster by restricting the number of codemods
            "--codemod-include=pixee:python/use-generator,pixee:python/use-defusedxml,pixee:python/use-walrus-if",
        ]
        if dry_run:
            args += ["--dry-run"]

        res = _run_cli(args)
        assert res == 0

        mock_reporting.assert_called_once()
        args_to_reporting = mock_reporting.call_args_list[0][0]
        assert len(args_to_reporting) == 4
        _, _, _, results_by_codemod = args_to_reporting

        assert len(results_by_codemod) == 3

        mock_reporting.return_value.write_report.assert_called_once()


class TestCliCodemodIncludeExclude:

    @mock.patch("codemodder.codetf.CodeTF.write_report")
    def test_codemod_include_no_match(self, write_report, dir_structure, caplog):
        bad_codemod = "doesntexist"
        code_dir, codetf = dir_structure
        args = [
            str(code_dir),
            "--output",
            str(codetf),
            f"--codemod-include={bad_codemod}",
        ]
        caplog.set_level(logging.INFO)

        _run_cli(args)
        write_report.assert_called_once()

        assert "no codemods to run" in caplog.text
        assert "scanned: 0 files" in caplog.text
        assert (
            f"Requested codemod to include '{bad_codemod}' does not exist."
            in caplog.text
        )

    @mock.patch("codemodder.codetf.CodeTF.write_report")
    def test_codemod_include_some_match(self, write_report, dir_structure, caplog):
        bad_codemod = "doesntexist"
        good_codemod = "pixee:python/secure-random"
        code_dir, codetf = dir_structure
        args = [
            str(code_dir),
            "--output",
            str(codetf),
            f"--codemod-include={bad_codemod},{good_codemod}",
        ]
        caplog.set_level(logging.INFO)
        _run_cli(args)
        write_report.assert_called_once()
        assert f"running codemod {good_codemod}" in caplog.text
        assert (
            f"Requested codemod to include '{bad_codemod}' does not exist."
            in caplog.text
        )

    @mock.patch("codemodder.codetf.CodeTF.write_report")
    def test_codemod_exclude_some_match(self, write_report, dir_structure, caplog):
        bad_codemod = "doesntexist"
        good_codemod = "secure-random"
        code_dir, codetf = dir_structure
        args = [
            str(code_dir),
            "--output",
            str(codetf),
            f"--codemod-exclude={bad_codemod},{good_codemod}",
        ]
        caplog.set_level(logging.INFO)
        _run_cli(args)
        write_report.assert_called_once()

        assert f"running codemod {good_codemod}" not in caplog.text
        assert "running codemod " in caplog.text

    @mock.patch("codemodder.codetf.CodeTF.write_report")
    @mock.patch("codemodder.codemods.base_codemod.BaseCodemod.apply")
    def test_codemod_exclude_no_match(self, apply, write_report, dir_structure, caplog):
        bad_codemod = "doesntexist"
        code_dir, codetf = dir_structure
        args = [
            str(code_dir),
            "--output",
            str(codetf),
            f"--codemod-exclude={bad_codemod}",
        ]
        caplog.set_level(logging.INFO)
        _run_cli(args)
        write_report.assert_called_once()
        assert "running codemod " in caplog.text

    @mock.patch("codemodder.codemods.semgrep.semgrep_run")
    def test_exclude_all_registered_codemods(self, mock_semgrep_run, dir_structure):
        code_dir, codetf = dir_structure
        assert not codetf.exists()

        registry = load_registered_codemods()
        names = ",".join(registry.ids)
        args = [
            str(code_dir),
            "--output",
            str(codetf),
            f"--codemod-exclude={names}",
        ]

        exit_code = _run_cli(args)
        assert exit_code == 0
        mock_semgrep_run.assert_not_called()
        assert codetf.exists()


class TestCliExitCode:
    @mock.patch("codemodder.codetf.CodeTF.write_report")
    def test_no_changes_success_0(self, mock_report, dir_structure):
        del mock_report
        code_dir, codetf = dir_structure
        args = [
            str(code_dir),
            "--output",
            "here.txt",
            "--codemod-include=pixee:python/url-sandbox",
            "--path-exclude",
            "*request.py",
        ]

        exit_code = _run_cli(args)
        assert exit_code == 0

    @mock.patch("codemodder.codetf.CodeTF.write_report")
    def test_bad_project_dir_1(self, mock_report):
        del mock_report
        args = [
            "bad/path/",
            "--output",
            "here.txt",
            "--codemod-include=pixee:python/url-sandbox",
        ]

        exit_code = _run_cli(args)
        assert exit_code == 1

    @mock.patch("codemodder.codetf.CodeTF.write_report")
    def test_conflicting_include_exclude(self, mock_report):
        del mock_report
        args = [
            "anything",
            "--output",
            "here.txt",
            "--codemod-exclude",
            "secure-random",
            "--codemod-include",
            "secure-random",
        ]
        with pytest.raises(SystemExit) as err:
            _run_cli(args)
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

    @pytest.mark.parametrize(
        "flag",
        [
            "sarif",
            "sonar-issues-json",
            "sonar-hotspots-json",
            "defectdojo-findings-json",
        ],
    )
    @mock.patch("codemodder.codetf.CodeTF.write_report")
    def test_bad_sarif_path(self, mock_report, caplog, flag):
        args = [
            "tests/samples",
            "--output",
            "here.txt",
            "--codemod-include=pixee:python/url-sandbox",
            f"--{flag}=bad.json",
        ]

        exit_code = _run_cli(args)
        assert exit_code == 1
        assert "No such file or directory: 'bad.json'" in caplog.text
        mock_report.assert_not_called()


class TestRun:
    @mock.patch("libcst.parse_module")
    def test_run_basic_call(self, mock_parse, dir_structure):
        code_dir, codetf = dir_structure

        codetf_output, status, token_usage = run(code_dir, dry_run=True)
        assert token_usage.total == 0
        assert status == 0
        assert codetf_output
        assert codetf_output.run.directory == str(code_dir)
        mock_parse.assert_not_called()
        assert not codetf.exists()

    @mock.patch("libcst.parse_module")
    def test_run_with_output(self, mock_parse, dir_structure):
        code_dir, codetf = dir_structure

        codetf_output, status, _ = run(
            code_dir,
            output=codetf,
            dry_run=True,
            codemod_include=["pixee:python/url-sandbox"],
        )
        assert status == 0
        assert codetf_output
        assert codetf_output.run.directory == str(code_dir)
        mock_parse.assert_not_called()
        assert codetf.exists()
