import yaml
from core_codemods.harden_pyyaml import HardenPyyaml
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestHardenPyyaml(BaseIntegrationTest):
    codemod = HardenPyyaml
    code_path = "tests/samples/unsafe_yaml.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [(3, "deserialized_data = yaml.load(data, Loader=yaml.SafeLoader)\n")],
    )
    expected_diff = '--- \n+++ \n@@ -1,4 +1,4 @@\n import yaml\n \n data = b"!!python/object/apply:subprocess.Popen \\\\n- ls"\n-deserialized_data = yaml.load(data, Loader=yaml.Loader)\n+deserialized_data = yaml.load(data, Loader=yaml.SafeLoader)\n'
    expected_line_change = "4"
    change_description = HardenPyyaml.CHANGE_DESCRIPTION
    # expected exception because the yaml.SafeLoader protects against unsafe code
    allowed_exceptions = (yaml.constructor.ConstructorError,)
