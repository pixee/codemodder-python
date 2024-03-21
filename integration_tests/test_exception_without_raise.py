from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.exception_without_raise import (
    ExceptionWithoutRaise,
    ExceptionWithoutRaiseTransformer,
)


class TestExceptionWithoutRaise(BaseIntegrationTest):
    codemod = ExceptionWithoutRaise
    original_code = """
    try:
        ValueError
    except:
        pass
    """
    replacement_lines = [(2, """    raise ValueError\n""")]
    # fmt: off
    expected_diff = (
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
