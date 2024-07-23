from codemodder.codemods.test import BaseIntegrationTest
from codemodder.dependency import DefusedXML
from core_codemods.use_defused_xml import UseDefusedXml, UseDefusedXmlTransformer


class TestUseDefusedXml(BaseIntegrationTest):
    codemod = UseDefusedXml
    original_code = """
    from io import StringIO
    from xml.etree import ElementTree, ElementInclude  # pylint: disable=unused-import
    
    xml = StringIO("<root>Hello XML</root>")
    et = ElementTree.parse(xml)
    """
    expected_new_code = """
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
+et = defusedxml.ElementTree.parse(xml)"""

    expected_line_change = "5"
    change_description = UseDefusedXmlTransformer.change_description
    requirements_file_name = "requirements.txt"
    original_requirements = (
        "# file used to test dependency management\n"
        "requests==2.31.0\n"
        "black==23.7.*\n"
        "mypy~=1.4\n"
        "pylint>1\n"
    )
    expected_requirements = (
        "# file used to test dependency management\n"
        "requests==2.31.0\n"
        "black==23.7.*\n"
        "mypy~=1.4\n"
        "pylint>1\n"
        f"{DefusedXML.requirement}\n"
    )
