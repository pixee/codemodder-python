from codemodder.codemods.test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)
from core_codemods.lxml_safe_parsing import LxmlSafeParsing


class TestLxmlSafeParsing(BaseIntegrationTest):
    codemod = LxmlSafeParsing
    code_path = "tests/samples/lxml_parsing.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (
                1,
                'lxml.etree.parse("path_to_file", parser=lxml.etree.XMLParser(resolve_entities=False))\n',
            ),
            (
                2,
                'lxml.etree.fromstring("xml_str", parser=lxml.etree.XMLParser(resolve_entities=False))\n',
            ),
        ],
    )
    expected_diff = '--- \n+++ \n@@ -1,3 +1,3 @@\n import lxml.etree\n-lxml.etree.parse("path_to_file")\n-lxml.etree.fromstring("xml_str")\n+lxml.etree.parse("path_to_file", parser=lxml.etree.XMLParser(resolve_entities=False))\n+lxml.etree.fromstring("xml_str", parser=lxml.etree.XMLParser(resolve_entities=False))\n'
    expected_line_change = "2"
    num_changes = 2
    change_description = LxmlSafeParsing.change_description
    allowed_exceptions = (OSError,)
