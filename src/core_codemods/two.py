import lxml.etree

parser = lxml.etree.XMLParser()
tree = lxml.etree.parse("xxe.xml", parser)
root = tree.getroot()
