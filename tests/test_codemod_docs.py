import pytest

from codemodder.codemods.api import BaseCodemod
from codemodder.registry import load_registered_codemods
from codemodder.scripts.generate_docs import METADATA


def pytest_generate_tests(metafunc):
    registry = load_registered_codemods()
    if "codemod" in metafunc.fixturenames:
        metafunc.parametrize("codemod", registry.codemods)


def test_load_codemod_docs_info(codemod: BaseCodemod):
    if codemod.name in ["order-imports"]:
        pytest.xfail(reason=f"{codemod.name} has no description")

    assert codemod.description
    assert codemod.review_guidance in (
        "Merge After Review",
        "Merge After Cursory Review",
        "Merge Without Review",
    )
    assert codemod.name in METADATA
