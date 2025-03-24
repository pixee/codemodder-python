from codemodder.codemods.test.integration_utils import BaseRemediationIntegrationTest
from core_codemods.lxml_safe_parsing import LxmlSafeParsing


class TestLxmlSafeParsing(BaseRemediationIntegrationTest):
    codemod = LxmlSafeParsing
    original_code = """
    import lxml.etree
    lxml.etree.parse("path_to_file")
    lxml.etree.fromstring("xml_str")
    """
    expected_lines_changed = [2, 3]
    expected_diff_per_change = [
        '--- \n+++ \n@@ -1,3 +1,3 @@\n import lxml.etree\n-lxml.etree.parse("path_to_file")\n+lxml.etree.parse("path_to_file", parser=lxml.etree.XMLParser(resolve_entities=False))\n lxml.etree.fromstring("xml_str")',
        '--- \n+++ \n@@ -1,3 +1,3 @@\n import lxml.etree\n lxml.etree.parse("path_to_file")\n-lxml.etree.fromstring("xml_str")\n+lxml.etree.fromstring("xml_str", parser=lxml.etree.XMLParser(resolve_entities=False))',
    ]
    num_changes = 2
    change_description = LxmlSafeParsing.change_description
    allowed_exceptions = (OSError,)
