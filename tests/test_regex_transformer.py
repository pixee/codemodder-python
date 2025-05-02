import logging

from sarif_pydantic import Sarif

from codemodder.codemods.regex_transformer import (
    RegexTransformerPipeline,
    SastRegexTransformerPipeline,
)
from codemodder.context import CodemodExecutionContext
from codemodder.file_context import FileContext
from codemodder.logging import OutputFormat, configure_logger
from codemodder.semgrep import SemgrepResult


def test_transformer_no_change(mocker, caplog, tmp_path_factory):
    configure_logger(True, OutputFormat.HUMAN)
    with caplog.at_level(logging.DEBUG):
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


def test_transformer_windows_carriage(mocker, tmp_path_factory):
    base_dir = tmp_path_factory.mktemp("foo")
    code = base_dir / "code.py"
    text = (
        b"Hello, world!\r\nThis is a test string with Windows-style line endings.\r\n"
    )
    code.write_bytes(text)

    file_context = FileContext(
        base_dir,
        code,
    )
    execution_context = CodemodExecutionContext(
        directory=base_dir,
        dry_run=False,
        verbose=False,
        registry=mocker.MagicMock(),
        providers=None,
        repo_manager=mocker.MagicMock(),
        path_include=[],
        path_exclude=[],
    )
    pipeline = RegexTransformerPipeline(
        pattern=r"world", replacement="Earth", change_description="testing"
    )

    changeset = pipeline.apply(
        context=execution_context,
        file_context=file_context,
        results=None,
    )
    assert changeset is not None
    assert code.read_bytes() == text.replace(b"world", b"Earth")
    assert changeset.changes[0].lineNumber == 1


def test_sast_transformer(mocker, tmp_path_factory):
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
    pipeline = SastRegexTransformerPipeline(
        pattern=r"hello", replacement="bye", change_description="testing"
    )

    data = Sarif.model_validate(
        {
            "runs": [
                {
                    "tool": {"driver": {"name": "Semgrep OSS"}},
                    "results": [
                        {
                            "guid": "e6e6f84a-0fac-472e-9215-4e31e6898f81",
                            "message": {"text": "message"},
                            "fingerprints": {"matchBasedId/v1": "123"},
                            "locations": [
                                {
                                    "ruleId": "rule",
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": "code.py",
                                            "uriBaseId": "%SRCROOT%",
                                        },
                                        "region": {
                                            "snippet": {"text": "snip"},
                                            "endColumn": 1,
                                            "endLine": 1,
                                            "startColumn": 1,
                                            "startLine": 1,
                                        },
                                    },
                                }
                            ],
                            "ruleId": "rule",
                        }
                    ],
                }
            ]
        }
    )
    sarif_run = data.runs[0]
    sarif_results = sarif_run.results or []
    results = [SemgrepResult.from_sarif(sarif_results[0], sarif_run)]

    changeset = pipeline.apply(
        context=execution_context,
        file_context=file_context,
        results=results,
    )
    assert changeset is not None
    assert code.read_text() == text.replace("hello", "bye")
    assert changeset.changes[0].lineNumber == 1
