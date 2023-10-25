from codemodder.file_context import FileContext


def test_file_context(mocker):
    directory = mocker.MagicMock()
    path = mocker.MagicMock()
    file_context = FileContext(directory, path)
    assert file_context.base_directory is directory
    assert file_context.file_path is path
    assert file_context.line_exclude == []
    assert file_context.line_include == []
