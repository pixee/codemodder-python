"""Module to store shared utilities for both unit and integration tests"""
import pytest
from codemodder import global_state


@pytest.fixture(autouse=True, scope="function")
def reset_global_directory():
    """
    Each test represents one full codemodder run. We want to prevent global
    state from leaking from one run to another.
    """
    yield
    global_state.set_directory("")
