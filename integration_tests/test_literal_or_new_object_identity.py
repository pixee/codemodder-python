from core_codemods.literal_or_new_object_identity import LiteralOrNewObjectIdentity
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestLiteralOrNewObjectIdentity(BaseIntegrationTest):
    codemod = LiteralOrNewObjectIdentity
    code_path = "tests/samples/literal_or_new_object_identity.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (1, """    return l == [1,2,3]\n"""),
        ],
    )

    # fmt: off
    expected_diff =(
    """--- \n"""
    """+++ \n"""
    """@@ -1,2 +1,2 @@\n"""
    """ def foo(l):\n"""
    """-    return l is [1,2,3]\n"""
    """+    return l == [1,2,3]\n"""

    )
    # fmt: on

    expected_line_change = "2"
    change_description = LiteralOrNewObjectIdentity.CHANGE_DESCRIPTION
    num_changed_files = 1
