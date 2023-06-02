# skip tests for now until we no longer test by mocking print
import pytest

pytest.skip(allow_module_level=True)
import mock
from codemodder.__main__ import parse_args, run


class TestUrlSandbox:
    @mock.patch("builtins.print")
    def test_result(self, mock_print):
        original_args = [
            "tests/samples/",
            "--output",
            "here.txt",
            "--codemod=url-sandbox",
        ]
        argv = parse_args(original_args)
        run(argv, original_args)
        calls = mock_print.call_args_list
        assert "import random" in calls[3][0][0]
        assert "import safe_requests" in calls[7][0][0]
