from lxml import etree

parser = etree.XMLParser(resolve_entities=False)
tree = etree.parse("xxe.xml", parser)
root = tree.getroot()
