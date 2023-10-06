from core_codemods.lxml_safe_parser_defaults import LxmlSafeParserDefaults
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestLxmlSafeParserDefaults(BaseIntegrationTest):
    codemod = LxmlSafeParserDefaults
    code_path = "tests/samples/lxml_parser.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path, [(1, "parser = lxml.etree.XMLParser(resolve_entities=False)\n")]
    )
    expected_diff = "--- \n+++ \n@@ -1,2 +1,2 @@\n import lxml.etree\n-parser = lxml.etree.XMLParser()\n+parser = lxml.etree.XMLParser(resolve_entities=False)\n"
    expected_line_change = "2"
    change_description = LxmlSafeParserDefaults.CHANGE_DESCRIPTION
