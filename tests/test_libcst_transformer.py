from pathlib import Path

import mock
from libcst._exceptions import ParserSyntaxError

from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.context import CodemodExecutionContext
from codemodder.file_context import FileContext
from core_codemods.defectdojo.results import DefectDojoResult
from core_codemods.sonar.results import SonarResult

FILE_PATH = mock.MagicMock()
DEFECTDOJO_RESULTS = [
    DefectDojoResult.from_result(
        {
            "id": 1,
            "title": "python.django.security.audit.secure-cookies.django-secure-set-cookie",
            "file_path": FILE_PATH,
            "line": 2,
        },
    )
]

SONAR_RESULTS = [
    SonarResult.from_result(
        {
            "rule": "python:S1716",
            "textRange": {
                "startLine": 1,
                "endLine": 1,
                "startOffset": 13,
                "endOffset": 14,
            },
            "component": FILE_PATH,
            "flows": [
                {
                    "locations": [
                        {
                            "component": FILE_PATH,
                            "textRange": {
                                "startLine": 1,
                                "endLine": 1,
                                "startOffset": 8,
                                "endOffset": 9,
                            },
                        }
                    ]
                }
            ],
            "status": "OPEN",
        }
    )
]


def _apply_and_assert(mocker, transformer):
    file_context = FileContext(Path("home"), FILE_PATH)
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
    pipeline = LibcstTransformerPipeline(transformer)
    pipeline.apply(
        context=execution_context,
        file_context=file_context,
        results=None,
    )
    assert len(file_context.failures) == 1
    assert file_context.unfixed_findings == []


def _apply_and_assert_with_tool(mocker, transformer, reason, results):
    file_context = FileContext(
        Path("home"),
        FILE_PATH,
        results=results,
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
        tool_result_files_map={"DOESNTMATTER": ["testing.json"]},
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
    return file_context


def test_parse_error(mocker, caplog):
    mocker.patch(
        "codemodder.codemods.libcst_transformer.cst.parse_module",
        side_effect=ParserSyntaxError,
    )
    transformer = mocker.MagicMock(spec=LibcstResultTransformer)
    _apply_and_assert(mocker, transformer)
    assert "Failed to parse file" in caplog.text


def test_transformer_error(mocker, caplog):
    transformer = mocker.MagicMock(spec=LibcstResultTransformer)
    transformer.transform.side_effect = ParserSyntaxError
    _apply_and_assert(mocker, transformer)
    assert "Failed to transform file" in caplog.text


def test_parse_error_with_defectdojo(mocker, caplog):
    mocker.patch(
        "codemodder.codemods.libcst_transformer.cst.parse_module",
        side_effect=ParserSyntaxError,
    )
    transformer = mocker.MagicMock(spec=LibcstResultTransformer)
    _apply_and_assert_with_tool(
        mocker, transformer, "Failed to parse file", DEFECTDOJO_RESULTS
    )
    assert "Failed to parse file" in caplog.text


def test_transformer_error_with_defectdojo(mocker, caplog):
    transformer = mocker.MagicMock(spec=LibcstResultTransformer)
    transformer.transform.side_effect = ParserSyntaxError
    _apply_and_assert_with_tool(
        mocker, transformer, "Failed to transform file", DEFECTDOJO_RESULTS
    )
    assert "Failed to transform file" in caplog.text


def test_transformer_error_with_sonar(mocker, caplog):
    transformer = mocker.MagicMock(spec=LibcstResultTransformer)
    transformer.transform.side_effect = ParserSyntaxError
    file_context = _apply_and_assert_with_tool(
        mocker, transformer, "Failed to transform file", SONAR_RESULTS
    )
    assert "Failed to transform file" in caplog.text
    assert (
        file_context.unfixed_findings[0].rule.url
        == "https://rules.sonarsource.com/python/RSPEC-1716/"
    )
