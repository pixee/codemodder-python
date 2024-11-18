from codemodder.registry import (
    CodemodCollection,
    CodemodRegistry,
    load_registered_codemods,
)


def test_default_extensions(mocker):
    registry = CodemodRegistry()
    assert registry.default_include_paths == []

    CodemodA = mocker.MagicMock(default_extensions=[".py"])
    CodemodB = mocker.MagicMock(default_extensions=[".py", ".txt"])

    registry.add_codemod_collection(
        CodemodCollection(origin="origin", codemods=[CodemodA, CodemodB])
    )

    assert sorted(registry.default_include_paths) == [
        "**/*.py",
        "**/*.txt",
        "*.py",
        "*.txt",
    ]


def test_codemods_by_tool(mocker):
    registry = CodemodRegistry()
    assert not registry._codemods_by_tool

    CodemodA = mocker.MagicMock()
    CodemodB = mocker.MagicMock()

    registry.add_codemod_collection(
        CodemodCollection(origin="origin", codemods=[CodemodA, CodemodB])
    )

    assert len(registry.codemods_by_tool("origin")) == 2


def test_current_codemods_by_tool():
    codemod_registry = load_registered_codemods()
    assert len(codemod_registry.codemods_by_tool("sonar")) > 0
    assert len(codemod_registry.codemods_by_tool("semgrep")) > 0
    assert len(codemod_registry.codemods_by_tool("pixee")) > 0
