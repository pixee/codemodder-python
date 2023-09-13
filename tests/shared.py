"""Module to store shared utilities for both unit and integration tests"""
import pytest
from codemodder import global_state
from codemodder.dependency_manager import DependencyManager


# TODO: should not have any global state
@pytest.fixture(autouse=True, scope="function")
def reset_global_state():
    """
    Each test represents one full codemodder run. We want to prevent global
    state from leaking from one run to another. This includes any data
    stored for codemods and global state from CLI run.
    """
    yield
    DependencyManager.clear_instance()
    global_state.set_directory("")
