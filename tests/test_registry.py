from codemodder.registry import CodemodCollection, CodemodRegistry


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
