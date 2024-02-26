import lxml.etree

parser = lxml.etree.XMLParser(resolve_entities=False)
tree = lxml.etree.parse("xxe.xml", parser)
root = tree.getroot()
