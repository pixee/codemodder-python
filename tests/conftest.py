import pytest
import mock


@pytest.fixture(autouse=True, scope="module")
def disable_file_writing():
    """
    Unit tests should not write output file.
    """
    patch_write_report = mock.patch("codemodder.__main__.write_report")
    patch_write_report.start()
    yield
    patch_write_report.stop()
