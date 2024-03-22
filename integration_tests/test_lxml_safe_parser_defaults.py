from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.lxml_safe_parser_defaults import LxmlSafeParserDefaults


class TestLxmlSafeParserDefaults(BaseIntegrationTest):
    codemod = LxmlSafeParserDefaults
    original_code = """
    import lxml.etree
    parser = lxml.etree.XMLParser()
    """
    replacement_lines = [(2, "parser = lxml.etree.XMLParser(resolve_entities=False)\n")]
    expected_diff = "--- \n+++ \n@@ -1,2 +1,2 @@\n import lxml.etree\n-parser = lxml.etree.XMLParser()\n+parser = lxml.etree.XMLParser(resolve_entities=False)\n"
    expected_line_change = "2"
    change_description = LxmlSafeParserDefaults.change_description
