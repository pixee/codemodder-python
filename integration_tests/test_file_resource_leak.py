from core_codemods.file_resource_leak import FileResourceLeak
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestFileResourceLeak(BaseIntegrationTest):
    codemod = FileResourceLeak
    code_path = "tests/samples/file_resource_leak.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (2, """with open(path, 'w', encoding='utf-8') as file:\n"""),
            (3, """    pass\n"""),
            (4, """    file.write('Hello World')\n"""),
        ],
    )

    # fmt: off
    expected_diff =(
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
    change_description = FileResourceLeak.CHANGE_DESCRIPTION
    num_changed_files = 1
