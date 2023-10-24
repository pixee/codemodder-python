from io import StringIO
from xml.etree import ElementTree, ElementInclude  # pylint: disable=unused-import

xml = StringIO("<root>Hello XML</root>")
et = ElementTree.parse(xml)
