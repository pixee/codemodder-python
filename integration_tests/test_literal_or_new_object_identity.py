from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.literal_or_new_object_identity import (
    LiteralOrNewObjectIdentity,
    LiteralOrNewObjectIdentityTransformer,
)


class TestLiteralOrNewObjectIdentity(BaseIntegrationTest):
    codemod = LiteralOrNewObjectIdentity
    original_code = """
    def foo(l):
        return l is [1,2,3]
    """
    replacement_lines = [(2, """    return l == [1,2,3]\n""")]

    # fmt: off
    expected_diff = (
    """--- \n"""
    """+++ \n"""
    """@@ -1,2 +1,2 @@\n"""
    """ def foo(l):\n"""
    """-    return l is [1,2,3]\n"""
    """+    return l == [1,2,3]\n"""

    )
    # fmt: on

    expected_line_change = "2"
    change_description = LiteralOrNewObjectIdentityTransformer.change_description
    num_changed_files = 1
