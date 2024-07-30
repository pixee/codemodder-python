import logging

from codemodder.codemods.regex_transformer import RegexTransformerPipeline
from codemodder.context import CodemodExecutionContext
from codemodder.file_context import FileContext


def test_transformer_no_change(mocker, caplog, tmp_path_factory):
    caplog.set_level(logging.DEBUG)
    base_dir = tmp_path_factory.mktemp("foo")
    code = base_dir / "code.py"
    code.write_text("# Something that won't match")

    file_context = FileContext(
        base_dir,
        code,
    )
    execution_context = CodemodExecutionContext(
        directory=base_dir,
        dry_run=True,
        verbose=False,
        registry=mocker.MagicMock(),
        providers=mocker.MagicMock(),
        repo_manager=mocker.MagicMock(),
        path_include=[],
        path_exclude=[],
    )
    pipeline = RegexTransformerPipeline(
        pattern=r"hello", replacement="bye", change_description="testing"
    )

    changeset = pipeline.apply(
        context=execution_context,
        file_context=file_context,
        results=None,
    )
    assert changeset is None
    assert "No changes produced for" in caplog.text


def test_transformer(mocker, tmp_path_factory):
    base_dir = tmp_path_factory.mktemp("foo")
    code = base_dir / "code.py"
    text = "# Something that will match pattern hello"
    code.write_text(text)

    file_context = FileContext(
        base_dir,
        code,
    )
    execution_context = CodemodExecutionContext(
        directory=base_dir,
        dry_run=False,
        verbose=False,
        registry=mocker.MagicMock(),
        providers=mocker.MagicMock(),
        repo_manager=mocker.MagicMock(),
        path_include=[],
        path_exclude=[],
    )
    pipeline = RegexTransformerPipeline(
        pattern=r"hello", replacement="bye", change_description="testing"
    )

    changeset = pipeline.apply(
        context=execution_context,
        file_context=file_context,
        results=None,
    )
    assert changeset is not None
    assert code.read_text() == text.replace("hello", "bye")
    assert changeset.changes[0].lineNumber == 1
