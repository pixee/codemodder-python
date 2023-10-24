import pytest
import mock


@pytest.fixture(autouse=True, scope="module")
def disable_write_report():
    """
    Unit tests should not write analysis report or update any source files.
    """
    patch_write_report = mock.patch(
        "codemodder.report.codetf_reporter.CodeTF.write_report"
    )

    patch_write_report.start()
    yield
    patch_write_report.stop()


@pytest.fixture(autouse=True, scope="module")
def disable_update_code():
    """
    Unit tests should not write analysis report or update any source files.
    """
    patch_update_code = mock.patch("codemodder.codemodder.update_code")
    patch_update_code.start()
    yield
    patch_update_code.stop()


@pytest.fixture(autouse=True, scope="module")
def disable_semgrep_run():
    """
    Semgrep run is slow so we mock them or pass hardcoded results when possible.
    """
    semgrep_run = mock.patch("codemodder.codemods.base_codemod.semgrep_run")

    semgrep_run.start()
    yield
    semgrep_run.stop()


@pytest.fixture(autouse=True, scope="module")
def disable_write_dependencies():
    """
    Unit tests should not write any dependency files
    """
    dm_write = mock.patch("codemodder.dependency_manager.DependencyManager.write")

    dm_write.start()
    yield
    dm_write.stop()


@pytest.fixture(scope="module")
def dir_with_pkg_managers(tmp_path_factory):
    base_dir = tmp_path_factory.mktemp("foo")
    req_file = base_dir / "requirements.txt"
    reqs = "# comment\nrequests==2.31.0\nblack==23.7.*\nmypy~=1.4\npylint>1\n"
    req_file.write_text(reqs)
    return base_dir
