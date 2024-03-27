from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.fix_missing_self_or_cls import (
    FixMissingSelfOrCls,
    FixMissingSelfOrClsTransformer,
)


class TestFixMissingSelfOrCls(BaseIntegrationTest):
    codemod = FixMissingSelfOrCls
    original_code = """
    class MyClass:
        def instance_method():
            print("instance_method")
    
        @classmethod
        def class_method():
            print("class_method")
    """
    replacement_lines = [
        (
            2,
            """    def instance_method(self):\n""",
        ),
        (
            6,
            """    def class_method(cls):\n""",
        ),
    ]
    # fmt: off
    expected_diff = (
    """--- \n"""
    """+++ \n"""
    """@@ -1,7 +1,7 @@\n"""
    """ class MyClass:\n"""
    """-    def instance_method():\n"""
    """+    def instance_method(self):\n"""
    """         print("instance_method")\n"""
    """ \n"""
    """     @classmethod\n"""
    """-    def class_method():\n"""
    """+    def class_method(cls):\n"""
    """         print("class_method")\n"""
    )
    # fmt: on

    expected_line_change = "2"
    change_description = FixMissingSelfOrClsTransformer.change_description
    num_changes = 2
