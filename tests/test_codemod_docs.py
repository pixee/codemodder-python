import pytest

from codemodder.__main__ import load_codemod_description
from codemodder.codemods import DEFAULT_CODEMODS


@pytest.fixture(params=DEFAULT_CODEMODS)
def codemod_name(request):
    name = request.param.name()
    if name in ["order-imports", "use-walrus-if"]:
        pytest.skip("No docs yet")
    return name


def test_load_codemod_description(codemod_name):  # pylint: disable=redefined-outer-name
    load_codemod_description(codemod_name)
