from codemodder.codemods.test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)
from core_codemods.fix_hasattr_call import TransformFixHasattrCall


class TestTransformFixHasattrCall(BaseIntegrationTest):
    codemod = TransformFixHasattrCall
    code_path = "tests/samples/fix_hasattr_call.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (4, """callable(obj)\n"""),
        ],
    )

    # fmt: off
    expected_diff =(
    """--- \n"""
    """+++ \n"""
    """@@ -2,4 +2,4 @@\n"""
    """     pass\n"""
    """ \n"""
    """ obj = Test()\n"""
    """-hasattr(obj, "__call__")\n"""
    """+callable(obj)\n"""
    )
    # fmt: on

    expected_line_change = "5"
    change_description = TransformFixHasattrCall.change_description
