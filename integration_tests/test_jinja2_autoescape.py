from codemodder.codemods.test.integration_utils import BaseRemediationIntegrationTest
from core_codemods.enable_jinja2_autoescape import (
    EnableJinja2Autoescape,
    EnableJinja2AutoescapeTransformer,
)


class TestEnableJinja2Autoescape(BaseRemediationIntegrationTest):
    codemod = EnableJinja2Autoescape
    original_code = """
    from jinja2 import Environment

    env = Environment()
    env = Environment(autoescape=False)
    """

    expected_diff_per_change = [
        "--- \n+++ \n@@ -1,4 +1,4 @@\n from jinja2 import Environment\n \n-env = Environment()\n+env = Environment(autoescape=True)\n env = Environment(autoescape=False)",
        "--- \n+++ \n@@ -1,4 +1,4 @@\n from jinja2 import Environment\n \n env = Environment()\n-env = Environment(autoescape=False)\n+env = Environment(autoescape=True)",
    ]

    expected_lines_changed = [3, 4]
    num_changes = 2
    change_description = EnableJinja2AutoescapeTransformer.change_description
