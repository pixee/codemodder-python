from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.lxml_safe_parsing import LxmlSafeParsing


class TestLxmlSafeParsing(BaseIntegrationTest):
    codemod = LxmlSafeParsing
    original_code = """
    import lxml.etree
    lxml.etree.parse("path_to_file")
    lxml.etree.fromstring("xml_str")
    """
    replacement_lines = [
        (
            2,
            'lxml.etree.parse("path_to_file", parser=lxml.etree.XMLParser(resolve_entities=False))\n',
        ),
        (
            3,
            'lxml.etree.fromstring("xml_str", parser=lxml.etree.XMLParser(resolve_entities=False))\n',
        ),
    ]
    expected_diff = '--- \n+++ \n@@ -1,3 +1,3 @@\n import lxml.etree\n-lxml.etree.parse("path_to_file")\n-lxml.etree.fromstring("xml_str")\n+lxml.etree.parse("path_to_file", parser=lxml.etree.XMLParser(resolve_entities=False))\n+lxml.etree.fromstring("xml_str", parser=lxml.etree.XMLParser(resolve_entities=False))\n'
    expected_line_change = "2"
    num_changes = 2
    change_description = LxmlSafeParsing.change_description
    allowed_exceptions = (OSError,)
