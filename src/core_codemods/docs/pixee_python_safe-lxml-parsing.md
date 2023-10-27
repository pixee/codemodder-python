This codemod sets the `parser` parameter in calls to  `lxml.etree.parse`  and `lxml.etree.fromstring` if omitted or set to `None` (the default value). Unfortunately, the default `parser=None` means `lxml` will rely on an unsafe parser, making your code potentially vulnerable to entity expansion attacks and external entity (XXE) attacks.

The changes look as follows:

```diff
  import lxml.etree
- lxml.etree.parse("path_to_file")
- lxml.etree.fromstring("xml_str")
+ lxml.etree.parse("path_to_file", parser=lxml.etree.XMLParser(resolve_entities=False))
+ lxml.etree.fromstring("xml_str", parser=lxml.etree.XMLParser(resolve_entities=False))
```
