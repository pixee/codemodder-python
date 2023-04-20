from src.main import parse_args, run


class TestSecureRandom:
    def test_result(self):
        argv = parse_args(["samples/", "here.json"])
        run(argv)
