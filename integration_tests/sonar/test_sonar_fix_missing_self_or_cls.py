from codemodder.codemods.test.integration_utils import SonarRemediationIntegrationTest
from core_codemods.fix_missing_self_or_cls import FixMissingSelfOrClsTransformer
from core_codemods.sonar.sonar_fix_missing_self_or_cls import SonarFixMissingSelfOrCls


class TestSonarFixMissingSelfOrCls(SonarRemediationIntegrationTest):
    codemod = SonarFixMissingSelfOrCls
    code_path = "tests/samples/fix_missing_self_or_cls.py"

    expected_diff_per_change = [
        '--- \n+++ \n@@ -1,5 +1,5 @@\n class MyClass:\n-    def instance_method():\n+    def instance_method(self):\n         print("instance_method")\n \n     @classmethod\n',
        '--- \n+++ \n@@ -3,5 +3,5 @@\n         print("instance_method")\n \n     @classmethod\n-    def class_method():\n+    def class_method(cls):\n         print("class_method")\n',
    ]

    expected_lines_changed = [2, 6]
    change_description = FixMissingSelfOrClsTransformer.change_description
    num_changes = 2
