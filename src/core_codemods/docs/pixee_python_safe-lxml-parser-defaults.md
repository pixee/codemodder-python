This codemod configures safe parameter values when initializing `lxml.etree.XMLParser`, `lxml.etree.ETCompatXMLParser`, `lxml.etree.XMLTreeBuilder`, or `lxml.etree.XMLPullParser`. If parameters `resolve_entities`, `no_network`, and `dtd_validation` are not set to safe values, your code may be vulnerable to entity expansion attacks and external entity (XXE) attacks.

Parameters `no_network` and `dtd_validation` have safe default values of `True` and `False`, respectively, so this codemod will set each to the default safe value if your code has assigned either to an unsafe value.

Parameter `resolve_entities` has an unsafe default value of `True`. This codemod will set `resolve_entities=False` if set to `True` or omitted.

The changes look as follows:

```diff
  import lxml.etree

- parser = lxml.etree.XMLParser()
- parser = lxml.etree.XMLParser(resolve_entities=True)
- parser = lxml.etree.XMLParser(resolve_entities=True, no_network=False, dtd_validation=True)
+ parser = lxml.etree.XMLParser(resolve_entities=False)
+ parser = lxml.etree.XMLParser(resolve_entities=False)
+ parser = lxml.etree.XMLParser(resolve_entities=False, no_network=True, dtd_validation=False)
```
