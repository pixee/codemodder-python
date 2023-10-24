from codemodder.file_context import FileContext


def test_file_context(mocker):
    file_context = FileContext(mocker.MagicMock())
    assert file_context.line_exclude == []
    assert file_context.line_include == []
