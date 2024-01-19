from core_codemods.remove_assertion_in_pytest_raises import (
    RemoveAssertionInPytestRaises,
    RemoveAssertionInPytestRaisesTransformer,
)
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestRemoveAssertionInPytestRaises(BaseIntegrationTest):
    codemod = RemoveAssertionInPytestRaises
    code_path = "tests/samples/remove_assertion_in_pytest_raises.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (5, """    assert 1\n"""),
            (6, """    assert 2\n"""),
        ],
    )

    # fmt: off
    expected_diff =(
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
