import pytest
import mock
from codemodder.codemods import DEFAULT_CODEMODS
from tests.shared import reset_global_state  # pylint: disable=unused-import

CODEMOD_NAMES = tuple(codemod.NAME for codemod in DEFAULT_CODEMODS)


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
    patch_update_code = mock.patch("codemodder.__main__.update_code")
    patch_update_code.start()
    yield
    patch_update_code.stop()


@pytest.fixture(autouse=True, scope="module")
def disable_semgrep_run():
    """
    Semgrep run is slow so unit tests should not run it. instead, if semgrep results
    are needed, mock them or pass hardcoded results
    """
    semgrep_run = mock.patch("codemodder.__main__.semgrep_run")

    semgrep_run.start()
    yield
    semgrep_run.stop()


@pytest.fixture(autouse=True, scope="module")
def disable_write_dependencies():
    """
    Unit tests should not write any dependency files
    """
    dm_write = mock.patch("codemodder.dependency_manager.DependencyManager._write")

    dm_write.start()
    yield
    dm_write.stop()
