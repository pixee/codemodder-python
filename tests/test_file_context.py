from codemodder.file_context import FileContext


def test_file_context():
    file_context = FileContext(None, None, None, None, None)
    assert file_context.line_exclude == []
    assert file_context.line_include == []
