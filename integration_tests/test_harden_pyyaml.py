from codemodder.codemods.harden_pyyaml import HardenPyyaml
from integration_tests.base_test import BaseIntegrationTest


class TestHardenPyyaml(BaseIntegrationTest):
    codemod = HardenPyyaml
    code_path = "tests/samples/unsafe_yaml.py"
    original_code = 'import yaml\n\ndata = b"!!python/object/apply:subprocess.Popen \\\\n- ls"\ndeserialized_data = yaml.load(data, Loader=yaml.Loader)\n'
    expected_new_code = 'import yaml\n\ndata = b"!!python/object/apply:subprocess.Popen \\\\n- ls"\ndeserialized_data = yaml.load(data, yaml.SafeLoader)\n'
    expected_diff = '--- \n+++ \n@@ -1,4 +1,4 @@\n import yaml\n \n data = b"!!python/object/apply:subprocess.Popen \\\\n- ls"\n-deserialized_data = yaml.load(data, Loader=yaml.Loader)\n+deserialized_data = yaml.load(data, yaml.SafeLoader)\n'
    expected_line_change = "4"
    change_description = HardenPyyaml.CHANGE_DESCRIPTION
