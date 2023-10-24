from core_codemods.use_defused_xml import UseDefusedXml
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestUseDefusedXml(BaseIntegrationTest):
    codemod = UseDefusedXml
    code_path = "tests/samples/use_defusedxml.py"

    original_code, _ = original_and_expected_from_code_path(code_path, [])
    expected_new_code = """\
from io import StringIO
from xml.etree import ElementInclude  # pylint: disable=unused-import
import defusedxml.ElementTree

xml = StringIO("<root>Hello XML</root>")
et = defusedxml.ElementTree.parse(xml)
"""

    num_changed_files = 2
    expected_diff = """\
--- 
+++ 
@@ -1,5 +1,6 @@
 from io import StringIO
-from xml.etree import ElementTree, ElementInclude  # pylint: disable=unused-import
+from xml.etree import ElementInclude  # pylint: disable=unused-import
+import defusedxml.ElementTree
 
 xml = StringIO("<root>Hello XML</root>")
-et = ElementTree.parse(xml)
+et = defusedxml.ElementTree.parse(xml)
"""

    expected_line_change = "5"
    change_description = UseDefusedXml.CHANGE_DESCRIPTION

    requirements_path = "tests/samples/requirements.txt"
    original_requirements = "# file used to test dependency management\nrequests==2.31.0\nblack==23.7.*\nmypy~=1.4\npylint>1\n"
    expected_new_reqs = "# file used to test dependency management\nrequests==2.31.0\nblack==23.7.*\nmypy~=1.4\npylint>1\ndefusedxml~=0.7.1\n"
