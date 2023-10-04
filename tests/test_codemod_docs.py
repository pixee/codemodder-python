import pytest

from codemodder.registry import load_registered_codemods


def pytest_generate_tests(metafunc):
    registry = load_registered_codemods()
    if "codemod" in metafunc.fixturenames:
        metafunc.parametrize("codemod", registry.codemods)


def test_load_codemod_description(codemod):
    if codemod.name in ["order-imports"]:
        pytest.xfail(reason="order-imports has no description")
    assert codemod._get_description() is not None  # pylint: disable=protected-access
