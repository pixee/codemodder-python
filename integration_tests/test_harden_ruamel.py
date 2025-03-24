from codemodder.codemods.test.integration_utils import BaseRemediationIntegrationTest
from core_codemods.harden_ruamel import HardenRuamel


class TestHardenRuamel(BaseRemediationIntegrationTest):
    codemod = HardenRuamel
    original_code = """
    from ruamel.yaml import YAML

    serializer = YAML(typ="unsafe")
    serializer = YAML(typ="base")
    """
    expected_diff_per_change = [
        '--- \n+++ \n@@ -1,4 +1,4 @@\n from ruamel.yaml import YAML\n \n-serializer = YAML(typ="unsafe")\n+serializer = YAML(typ="safe")\n serializer = YAML(typ="base")',
        '--- \n+++ \n@@ -1,4 +1,4 @@\n from ruamel.yaml import YAML\n \n serializer = YAML(typ="unsafe")\n-serializer = YAML(typ="base")\n+serializer = YAML(typ="safe")',
    ]

    expected_lines_changed = [3, 4]
    num_changes = 2
    change_description = HardenRuamel.change_description
