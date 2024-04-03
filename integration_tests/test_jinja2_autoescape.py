from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.enable_jinja2_autoescape import (
    EnableJinja2Autoescape,
    EnableJinja2AutoescapeTransformer,
)


class TestEnableJinja2Autoescape(BaseIntegrationTest):
    codemod = EnableJinja2Autoescape
    original_code = """
    from jinja2 import Environment

    env = Environment()
    env = Environment(autoescape=False)
    """
    replacement_lines = [
        (3, "env = Environment(autoescape=True)\n"),
        (4, "env = Environment(autoescape=True)\n"),
    ]
    expected_diff = "--- \n+++ \n@@ -1,4 +1,4 @@\n from jinja2 import Environment\n \n-env = Environment()\n-env = Environment(autoescape=False)\n+env = Environment(autoescape=True)\n+env = Environment(autoescape=True)\n"
    expected_line_change = "3"
    num_changes = 2
    change_description = EnableJinja2AutoescapeTransformer.change_description
