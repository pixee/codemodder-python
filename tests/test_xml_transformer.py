from io import StringIO
from textwrap import dedent
from xml.sax import handler

import pytest
from defusedxml import ExternalReferenceForbidden
from defusedxml.sax import make_parser

from codemodder.codemods.xml_transformer import (
    ElementAttributeXMLTransformer,
    XMLTransformer,
)


class TestXMLTransformer:

    def run_and_assert(self, input_code, expected_output):
        with StringIO() as result, StringIO(dedent(input_code)) as input_stream:
            result = StringIO()
            transformer = XMLTransformer(result)
            parser = make_parser()
            parser.setContentHandler(transformer)
            parser.setProperty(handler.property_lexical_handler, transformer)
            parser.parse(input_stream)
            assert result.getvalue() == dedent(expected_output)

    def test_parse_dtd_forbidden(self):
        input_code = """\
                <?xml version="1.0" encoding="utf-8"?>
                <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        """
        expected_output = input_code
        with pytest.raises(ExternalReferenceForbidden):
            self.run_and_assert(input_code, expected_output)

    def test_parse_comment(self):
        input_code = """\
                <?xml version="1.0" encoding="utf-8"?>
                <!-- comment -->
                <element></element>"""
        expected_output = input_code
        self.run_and_assert(input_code, expected_output)

    def test_parse_cdata(self):
        input_code = """\
                <?xml version="1.0" encoding="utf-8"?>
                <element>
                    <![CDATA[some characters]]>
                </element>"""
        expected_output = input_code
        self.run_and_assert(input_code, expected_output)


class TestElementAttributeXMLTransformer:

    def run_and_assert(self, name_attr_map, input_code, expected_output):
        with StringIO() as result, StringIO(dedent(input_code)) as input_stream:
            result = StringIO()
            transformer = ElementAttributeXMLTransformer(
                result, name_attributes_map=name_attr_map
            )
            parser = make_parser()
            parser.setContentHandler(transformer)
            parser.setProperty(handler.property_lexical_handler, transformer)
            parser.parse(input_stream)
            assert result.getvalue() == dedent(expected_output)

    def test_change_single_attr(self):
        input_code = """\
                <?xml version="1.0" encoding="utf-8"?>
                <element attr="false"></element>"""
        expected_output = """\
                <?xml version="1.0" encoding="utf-8"?>
                <element attr="true"></element>"""
        name_attr_map = {"element": {"attr": "true"}}
        self.run_and_assert(name_attr_map, input_code, expected_output)

    def test_change_multiple_attr(self):
        input_code = """\
                <?xml version="1.0" encoding="utf-8"?>
                <element first="1" second="2"></element>"""
        expected_output = """\
                <?xml version="1.0" encoding="utf-8"?>
                <element first="one" second="two"></element>"""
        name_attr_map = {"element": {"first": "one", "second": "two"}}
        self.run_and_assert(name_attr_map, input_code, expected_output)
