from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.harden_ruamel import HardenRuamel


class TestHardenRuamel(BaseIntegrationTest):
    codemod = HardenRuamel
    original_code = """
    from ruamel.yaml import YAML

    serializer = YAML(typ="unsafe")
    serializer = YAML(typ="base")
    """
    replacement_lines = [
        (3, 'serializer = YAML(typ="safe")\n'),
        (4, 'serializer = YAML(typ="safe")\n'),
    ]
    expected_diff = '--- \n+++ \n@@ -1,4 +1,4 @@\n from ruamel.yaml import YAML\n \n-serializer = YAML(typ="unsafe")\n-serializer = YAML(typ="base")\n+serializer = YAML(typ="safe")\n+serializer = YAML(typ="safe")\n'
    expected_line_change = "3"
    num_changes = 2
    change_description = HardenRuamel.change_description
