import pytest
import mock


@pytest.fixture(autouse=True, scope="module")
def disable_file_writing():
    """
    Unit tests should not write analysis report or update any source files.
    """
    patch_write_report = mock.patch(
        "codemodder.report.codetf_reporter.CodeTF.write_report"
    )
    patch_update_code = mock.patch("codemodder.__main__.update_code")
    patch_write_report.start()
    patch_update_code.start()
    yield
    patch_write_report.stop()
    patch_update_code.stop()
