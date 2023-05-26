import mock
from codemodder.__main__ import parse_args, run


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
