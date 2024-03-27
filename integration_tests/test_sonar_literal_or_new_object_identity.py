from codemodder.codemods.test import SonarIntegrationTest
from core_codemods.literal_or_new_object_identity import (
    LiteralOrNewObjectIdentityTransformer,
)
from core_codemods.sonar.sonar_literal_or_new_object_identity import (
    SonarLiteralOrNewObjectIdentity,
)


class TestLiteralOrNewObjectIdentity(SonarIntegrationTest):
    codemod = SonarLiteralOrNewObjectIdentity
    code_path = "tests/samples/literal_or_new_object_identity.py"
    replacement_lines = [
        (2, """    return l == [1,2,3]\n"""),
    ]

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
