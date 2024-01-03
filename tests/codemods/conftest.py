import pytest


@pytest.fixture(autouse=True)
def disable_semgrep_run():
    """
    Override the fixture defined in conftest.py
    """


@pytest.fixture(autouse=True)
def disable_update_code():
    """
    Override the fixture defined in conftest.py
    """
