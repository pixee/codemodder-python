from lxml import etree

parser = etree.XMLParser()
tree = etree.parse("xxe.xml", parser)
root = tree.getroot()
