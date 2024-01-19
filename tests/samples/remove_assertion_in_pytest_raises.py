import pytest

def test_foo():
    with pytest.raises(ZeroDivisionError):
        error = 1/0
        assert 1
        assert 2
