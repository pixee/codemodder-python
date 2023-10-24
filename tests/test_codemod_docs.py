import pytest

from codemodder.registry import load_registered_codemods
from codemodder.scripts.generate_docs import METADATA


def pytest_generate_tests(metafunc):
    registry = load_registered_codemods()
    if "codemod" in metafunc.fixturenames:
        metafunc.parametrize("codemod", registry.codemods)


def test_load_codemod_docs_info(codemod):
    if codemod.name in ["order-imports"]:
        pytest.xfail(reason="order-imports has no description")
    assert codemod._get_description() is not None  # pylint: disable=protected-access
    assert codemod.review_guidance in (
        "Merge After Review",
        "Merge After Cursory Review",
        "Merge Without Review",
    )
    assert codemod.name in METADATA
