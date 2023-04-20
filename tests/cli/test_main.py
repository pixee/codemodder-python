import pytest
from src.main import parse_args


class TestParseArgs:
    def test_no_args(self):
        with pytest.raises(SystemExit) as err:
            parse_args([])
        assert (
            err.value.args[0]
            == "the following arguments are required: directory, output"
        )
