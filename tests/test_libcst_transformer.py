from libcst._exceptions import ParserSyntaxError

from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.context import CodemodExecutionContext
from codemodder.file_context import FileContext
from core_codemods.defectdojo.results import DefectDojoResult


def _apply_and_assert(mocker, transformer):
    file_context = FileContext("home", mocker.MagicMock())
    execution_context = CodemodExecutionContext(
        directory=mocker.MagicMock(),
        dry_run=True,
        verbose=False,
        registry=mocker.MagicMock(),
        repo_manager=mocker.MagicMock(),
        path_include=[],
        path_exclude=[],
    )
    pipeline = LibcstTransformerPipeline(transformer)
    pipeline.apply(
        context=execution_context,
        file_context=file_context,
        results=None,
    )
    assert len(file_context.failures) == 1
    assert file_context.unfixed_findings == []


def _apply_and_assert_with_tool(mocker, transformer, reason):
    file_path = mocker.MagicMock()
    file_context = FileContext(
        "home",
        file_path,
        results=[
            DefectDojoResult.from_finding(
                {
                    "id": 1,
                    "title": "python.django.security.audit.secure-cookies.django-secure-set-cookie",
                    "file_path": file_path,
                    "line": 2,
                },
            )
        ],
    )
    execution_context = CodemodExecutionContext(
        directory=mocker.MagicMock(),
        dry_run=True,
        verbose=False,
        registry=mocker.MagicMock(),
        repo_manager=mocker.MagicMock(),
        path_include=[],
        path_exclude=[],
        tool_result_files_map={"sonar": ["results.json"]},
    )
    pipeline = LibcstTransformerPipeline(transformer)
    pipeline.apply(
        context=execution_context,
        file_context=file_context,
        results=None,
    )
    assert len(file_context.failures) == 1
    assert len(file_context.unfixed_findings) == 1
    assert file_context.unfixed_findings[0].reason == reason


def test_parse_error(mocker, caplog):
    mocker.patch(
        "codemodder.codemods.libcst_transformer.cst.parse_module",
        side_effect=ParserSyntaxError,
    )
    transformer = mocker.MagicMock(spec=LibcstResultTransformer)
    _apply_and_assert(mocker, transformer)
    assert "error parsing file" in caplog.text


def test_transformer_error(mocker, caplog):
    transformer = mocker.MagicMock(spec=LibcstResultTransformer)
    transformer.transform.side_effect = ParserSyntaxError
    _apply_and_assert(mocker, transformer)
    assert "error transforming file" in caplog.text


def test_parse_error_with_tool(mocker, caplog):
    mocker.patch(
        "codemodder.codemods.libcst_transformer.cst.parse_module",
        side_effect=ParserSyntaxError,
    )
    transformer = mocker.MagicMock(spec=LibcstResultTransformer)
    _apply_and_assert_with_tool(mocker, transformer, "parsing file")
    assert "error parsing file" in caplog.text


def test_transformer_error_with_tool(mocker, caplog):
    transformer = mocker.MagicMock(spec=LibcstResultTransformer)
    transformer.transform.side_effect = ParserSyntaxError
    _apply_and_assert_with_tool(mocker, transformer, "transforming file")
    assert "error transforming file" in caplog.text
