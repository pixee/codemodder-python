from codemodder.codemods.test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)
from core_codemods.exception_without_raise import (
    ExceptionWithoutRaise,
    ExceptionWithoutRaiseTransformer,
)


class TestExceptionWithoutRaise(BaseIntegrationTest):
    codemod = ExceptionWithoutRaise
    code_path = "tests/samples/exception_without_raise.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (1, """    raise ValueError\n"""),
        ],
    )

    # fmt: off
    expected_diff =(
    """--- \n"""
    """+++ \n"""
    """@@ -1,4 +1,4 @@\n"""
    """ try:\n"""
    """-    ValueError\n"""
    """+    raise ValueError\n"""
    """ except:\n"""
    """     pass\n"""
    )
    # fmt: on

    expected_line_change = "2"
    change_description = ExceptionWithoutRaiseTransformer.change_description
    num_changed_files = 1
