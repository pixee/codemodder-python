from lxml import etree
import lxml.etree

parser = etree.XMLParser(resolve_entities=False)
tree = etree.parse("xxe.xml", parser, parser=lxml.etree.XMLParser(resolve_entities=False))
root = tree.getroot()
