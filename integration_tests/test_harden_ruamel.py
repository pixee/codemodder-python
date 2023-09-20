from core_codemods.harden_ruamel import HardenRuamel
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestHardenRuamel(BaseIntegrationTest):
    codemod = HardenRuamel
    code_path = "tests/samples/unsafe_ruamel.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (2, 'serializer = YAML(typ="safe")\n'),
            (3, 'serializer = YAML(typ="safe")\n'),
        ],
    )
    expected_diff = '--- \n+++ \n@@ -1,4 +1,4 @@\n from ruamel.yaml import YAML\n \n-serializer = YAML(typ="unsafe")\n-serializer = YAML(typ="base")\n+serializer = YAML(typ="safe")\n+serializer = YAML(typ="safe")\n'
    expected_line_change = "3"
    num_changes = 2
    change_description = HardenRuamel.CHANGE_DESCRIPTION
