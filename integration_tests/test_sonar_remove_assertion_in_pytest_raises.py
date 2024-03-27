from codemodder.codemods.test import SonarIntegrationTest
from core_codemods.remove_assertion_in_pytest_raises import (
    RemoveAssertionInPytestRaisesTransformer,
)
from core_codemods.sonar.sonar_remove_assertion_in_pytest_raises import (
    SonarRemoveAssertionInPytestRaises,
)


class TestSonarRemoveAssertionInPytestRaises(SonarIntegrationTest):
    codemod = SonarRemoveAssertionInPytestRaises
    code_path = "tests/samples/remove_assertion_in_pytest_raises.py"
    replacement_lines = [
        (6, """    assert 1\n"""),
        (7, """    assert 2\n"""),
    ]

    # fmt: off
    expected_diff = (
    """--- \n"""
    """+++ \n"""
    """@@ -3,5 +3,5 @@\n"""
    """ def test_foo():\n"""
    """     with pytest.raises(ZeroDivisionError):\n"""
    """         error = 1/0\n"""
    """-        assert 1\n"""
    """-        assert 2\n"""
    """+    assert 1\n"""
    """+    assert 2\n"""
    )
    # fmt: on

    expected_line_change = "4"
    change_description = RemoveAssertionInPytestRaisesTransformer.change_description
    num_changed_files = 1
    num_changes = 1
