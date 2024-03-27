from codemodder.codemods.test import SonarIntegrationTest
from core_codemods.exception_without_raise import ExceptionWithoutRaiseTransformer
from core_codemods.sonar.sonar_exception_without_raise import SonarExceptionWithoutRaise


class TestSonarExceptionWithoutRaise(SonarIntegrationTest):
    codemod = SonarExceptionWithoutRaise
    code_path = "tests/samples/exception_without_raise.py"
    replacement_lines = [
        (2, """    raise ValueError\n"""),
    ]
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
