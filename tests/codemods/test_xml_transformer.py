from pathlib import Path

from codemodder.codemods.xml_transformer import (
    ElementAttributeXMLTransformer,
    XMLTransformerPipeline,
)
from codemodder.context import CodemodExecutionContext
from codemodder.file_context import FileContext


def test_transformer_failure(mocker, caplog):
    mocker.patch(
        "defusedxml.expatreader.DefusedExpatParser.parse",
        side_effect=Exception,
    )
    file_context = FileContext(
        Path("home"),
        Path("test.xml"),
    )
    execution_context = CodemodExecutionContext(
        directory=mocker.MagicMock(),
        dry_run=True,
        verbose=False,
        registry=mocker.MagicMock(),
        providers=None,
        repo_manager=mocker.MagicMock(),
        path_include=[],
        path_exclude=[],
    )
    transformer = mocker.MagicMock(spec=ElementAttributeXMLTransformer)
    pipeline = XMLTransformerPipeline(transformer)

    changeset = pipeline.apply(
        context=execution_context,
        file_context=file_context,
        results=None,
    )
    assert changeset is None
    assert "Failed to parse XML file" in caplog.text


def test_transformer(mocker):
    mocker.patch(
        "defusedxml.expatreader.DefusedExpatParser.parse",
    )
    mocker.patch("builtins.open")
    mocker.patch("codemodder.codemods.xml_transformer.create_diff", return_value="diff")
    file_context = FileContext(
        parent_dir := Path("home"),
        parent_dir / Path("test.xml"),
    )
    execution_context = CodemodExecutionContext(
        directory=parent_dir,
        dry_run=True,
        verbose=False,
        registry=mocker.MagicMock(),
        providers=None,
        repo_manager=mocker.MagicMock(),
        path_include=[],
        path_exclude=[],
    )
    transformer = mocker.MagicMock(spec=ElementAttributeXMLTransformer)
    transformer.changes = ["change1", "change2"]
    pipeline = XMLTransformerPipeline(transformer)

    changeset = pipeline.apply(
        context=execution_context,
        file_context=file_context,
        results=None,
    )
    assert changeset is not None
