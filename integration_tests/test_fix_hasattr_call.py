from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.fix_hasattr_call import TransformFixHasattrCall


class TestTransformFixHasattrCall(BaseIntegrationTest):
    codemod = TransformFixHasattrCall
    original_code = """
    class Test:
        pass
    
    obj = Test()
    hasattr(obj, "__call__")
    """

    replacement_lines = [
        (5, """callable(obj)\n"""),
    ]

    # fmt: off
    expected_diff = (
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
