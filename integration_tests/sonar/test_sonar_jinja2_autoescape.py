from codemodder.codemods.test.integration_utils import SonarRemediationIntegrationTest
from core_codemods.enable_jinja2_autoescape import EnableJinja2AutoescapeTransformer
from core_codemods.sonar.sonar_enable_jinja2_autoescape import (
    SonarEnableJinja2Autoescape,
)


class TestSonarEnableJinja2Autoescape(SonarRemediationIntegrationTest):
    codemod = SonarEnableJinja2Autoescape
    code_path = "tests/samples/jinja2_autoescape.py"
    expected_diff_per_change = [
        "--- \n+++ \n@@ -1,4 +1,4 @@\n from jinja2 import Environment\n \n-env = Environment()\n+env = Environment(autoescape=True)\n env = Environment(autoescape=False)\n",
        "--- \n+++ \n@@ -1,4 +1,4 @@\n from jinja2 import Environment\n \n env = Environment()\n-env = Environment(autoescape=False)\n+env = Environment(autoescape=True)\n",
    ]

    expected_lines_changed = [3, 4]
    num_changes = 2
    change_description = EnableJinja2AutoescapeTransformer.change_description
