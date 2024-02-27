from core_codemods.use_defused_xml import UseDefusedXml
from codemodder.codemods.test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)
from codemodder.dependency import DefusedXML


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
    change_description = UseDefusedXml.change_description

    requirements_path = "tests/samples/requirements.txt"
    original_requirements = "# file used to test dependency management\nrequests==2.31.0\nblack==23.7.*\nmypy~=1.4\npylint>1\n"
    expected_new_reqs = (
        f"# file used to test dependency management\n"
        "requests==2.31.0\n"
        "black==23.7.*\n"
        "mypy~=1.4\n"
        "pylint>1\n"
        f"{DefusedXML.requirement} \\\n"
        f"{DefusedXML.build_hashes()}"
    )
