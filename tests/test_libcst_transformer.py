from libcst._exceptions import ParserSyntaxError

from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)


def test_parse_error(mocker, caplog):
    mocker.patch(
        "codemodder.codemods.libcst_transformer.cst.parse_module",
        side_effect=ParserSyntaxError,
    )

    transformer = mocker.MagicMock(spec=LibcstResultTransformer)
    file_context = mocker.MagicMock()

    pipeline = LibcstTransformerPipeline(transformer)
    pipeline.apply(
        context=mocker.MagicMock(),
        file_context=file_context,
        results=None,
    )

    file_context.add_failure.assert_called_once()
    assert "error parsing file" in caplog.text


def test_transformer_error(mocker, caplog):
    transformer = mocker.MagicMock(spec=LibcstResultTransformer)
    transformer.transform.side_effect = ParserSyntaxError
    file_context = mocker.MagicMock()

    pipeline = LibcstTransformerPipeline(transformer)
    pipeline.apply(
        context=mocker.MagicMock(),
        file_context=file_context,
        results=None,
    )

    file_context.add_failure.assert_called_once()
    assert "error transforming file" in caplog.text
