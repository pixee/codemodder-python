from core_codemods.enable_jinja2_autoescape import EnableJinja2Autoescape
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestEnableJinja2Autoescape(BaseIntegrationTest):
    codemod = EnableJinja2Autoescape
    code_path = "tests/samples/jinja2_autoescape.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (2, "env = Environment(autoescape=True)\n"),
            (3, "env = Environment(autoescape=True)\n"),
        ],
    )
    expected_diff = "--- \n+++ \n@@ -1,4 +1,4 @@\n from jinja2 import Environment\n \n-env = Environment()\n-env = Environment(autoescape=False)\n+env = Environment(autoescape=True)\n+env = Environment(autoescape=True)\n"
    expected_line_change = "3"
    num_changes = 2
    change_description = EnableJinja2Autoescape.CHANGE_DESCRIPTION
