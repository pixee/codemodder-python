import mock
import pytest
from codemodder.__main__ import parse_args, run


@pytest.fixture(autouse=True, scope="module")
def disable_file_writing():
    """
    The tests in this module should not write the output file for ease of testing.
    """
    patch_write_report = mock.patch("codemodder.__main__.write_report")
    patch_write_report.start()
    yield
    patch_write_report.stop()


class TestSecureRandom:
    @mock.patch("builtins.print")
    def test_result(self, mock_print):
        argv = parse_args(
            ["tests/samples/", "--output", "here.txt", "--codemod=secure-random"]
        )
        run(argv)
        calls = mock_print.call_args_list
        assert "import secrets" in calls[3][0][0]
        assert "import requests" in calls[5][0][0]
