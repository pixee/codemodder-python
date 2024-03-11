from codemodder.codemods.test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)
from core_codemods.fix_missing_self_or_cls import FixMissingSelfOrClsTransformer
from core_codemods.sonar.sonar_fix_missing_self_or_cls import SonarFixMissingSelfOrCls


class TestSonarFixMissingSelfOrCls(BaseIntegrationTest):
    codemod = SonarFixMissingSelfOrCls
    code_path = "tests/samples/fix_missing_self_or_cls.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (
                1,
                """    def instance_method(self):\n""",
            ),
            (
                5,
                """    def class_method(cls):\n""",
            ),
        ],
    )
    sonar_issues_json = "tests/samples/sonar_issues.json"
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
