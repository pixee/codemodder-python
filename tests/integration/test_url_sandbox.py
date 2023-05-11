import mock
from codemodder.__main__ import parse_args, run


class TestUrlSandbox:
    @mock.patch("builtins.print")
    def test_result(self, mock_print):
        argv = parse_args(
            ["tests/samples/", "--output", "here.txt", "--codemod=url-sandbox"]
        )
        run(argv)
        calls = mock_print.call_args_list
        assert "import random" in calls[3][0][0]
        assert "import safe_requests" in calls[7][0][0]
