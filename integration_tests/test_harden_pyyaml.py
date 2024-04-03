import yaml

from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.harden_pyyaml import HardenPyyaml, HardenPyyamlTransformer


class TestHardenPyyaml(BaseIntegrationTest):
    codemod = HardenPyyaml
    original_code = """
    import yaml

    data = b"!!python/object/apply:subprocess.Popen \\\\n- ls"
    deserialized_data = yaml.load(data, Loader=yaml.Loader)
    """
    replacement_lines = [
        (4, "deserialized_data = yaml.load(data, Loader=yaml.SafeLoader)\n")
    ]
    expected_diff = '--- \n+++ \n@@ -1,4 +1,4 @@\n import yaml\n \n data = b"!!python/object/apply:subprocess.Popen \\\\n- ls"\n-deserialized_data = yaml.load(data, Loader=yaml.Loader)\n+deserialized_data = yaml.load(data, Loader=yaml.SafeLoader)\n'
    expected_line_change = "4"
    change_description = HardenPyyamlTransformer.change_description
    # expected exception because the yaml.SafeLoader protects against unsafe code
    allowed_exceptions = (yaml.constructor.ConstructorError,)
