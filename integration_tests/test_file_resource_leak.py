from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.file_resource_leak import (
    FileResourceLeak,
    FileResourceLeakTransformer,
)


class TestFileResourceLeak(BaseIntegrationTest):
    codemod = FileResourceLeak
    original_code = """
    import tempfile
    path = tempfile.NamedTemporaryFile().name
    file = open(path, 'w', encoding='utf-8')
    pass
    file.write('Hello World')
    """
    replacement_lines = [
        (3, """with open(path, 'w', encoding='utf-8') as file:\n"""),
        (4, """    pass\n"""),
        (5, """    file.write('Hello World')\n"""),
    ]
    # fmt: off
    expected_diff = (
    """--- \n"""
    """+++ \n"""
    """@@ -1,5 +1,5 @@\n"""
    """ import tempfile\n"""
    """ path = tempfile.NamedTemporaryFile().name\n"""
    """-file = open(path, 'w', encoding='utf-8')\n"""
    """-pass\n"""
    """-file.write('Hello World')\n"""
    """+with open(path, 'w', encoding='utf-8') as file:\n"""
    """+    pass\n"""
    """+    file.write('Hello World')\n""")
    # fmt: on

    expected_line_change = "3"
    change_description = FileResourceLeakTransformer.change_description
    num_changed_files = 1
