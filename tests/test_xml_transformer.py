from io import StringIO
from textwrap import dedent
from xml.sax import handler

import pytest
from defusedxml import ExternalReferenceForbidden
from defusedxml.sax import make_parser

from codemodder.codemods.xml_transformer import (
    ElementAttributeXMLTransformer,
    NewElement,
    NewElementXMLTransformer,
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

    def test_add_new_attribute(self):
        input_code = """\
                <?xml version="1.0" encoding="utf-8"?>
                <element></element>"""
        expected_output = """\
                <?xml version="1.0" encoding="utf-8"?>
                <element attr="true"></element>"""
        name_attr_map = {"element": {"attr": "true"}}
        self.run_and_assert(name_attr_map, input_code, expected_output)

    def test_change_multiple_attr_and_preserve_existing(self):
        input_code = """\
                <?xml version="1.0" encoding="utf-8"?>
                <element first="1" second="2" three="three"></element>"""
        expected_output = """\
                <?xml version="1.0" encoding="utf-8"?>
                <element first="one" second="two" three="three"></element>"""
        name_attr_map = {"element": {"first": "one", "second": "two"}}
        self.run_and_assert(name_attr_map, input_code, expected_output)


class TestNewElementXMLTransformer:

    def run_and_assert(self, new_elements, input_code, expected_output):
        with StringIO() as result, StringIO(dedent(input_code)) as input_stream:
            result = StringIO()
            transformer = NewElementXMLTransformer(result, new_elements=new_elements)
            parser = make_parser()
            parser.setContentHandler(transformer)
            parser.setProperty(handler.property_lexical_handler, transformer)
            parser.parse(input_stream)
            assert result.getvalue() == dedent(expected_output)

    def test_add_new_element(self):
        input_code = """\
                <root></root>
        """
        expected_output = """\
                <?xml version="1.0" encoding="utf-8"?>
                <root><child1></child1><child2 one="1">2</child2></root>"""
        new_elements = [
            NewElement(name="child1", parent_name="root"),
            NewElement(
                name="child2", parent_name="root", content="2", attributes={"one": "1"}
            ),
        ]
        self.run_and_assert(new_elements, input_code, expected_output)

    def test_add_new_sibling_same_name(self):
        input_code = """\
                <root>
                    <child>child 1</child>
                </root>
        """
        expected_output = """\
                <?xml version="1.0" encoding="utf-8"?>
                <root>
                    <child>child 1</child>
                <child>child 2</child></root>"""
        new_elements = [
            NewElement(name="child", parent_name="root", content="child 2"),
        ]
        self.run_and_assert(new_elements, input_code, expected_output)

    # def add_new_sibling_same_name(self):
    #     input_code = """\
    #             <?xml version="1.0" encoding="UTF-8"?>
    #             <library>
    #                 <book>
    #                     <title>The Great Gatsby</title>
    #                     <author>F. Scott Fitzgerald</author>
    #                 </book>
    #             </library>
    #     """
    #     expected_output = """\
    #             <?xml version="1.0" encoding="UTF-8"?>
    #             <library>
    #                 <book>
    #                     <title>The Great Gatsby</title>
    #                     <author>F. Scott Fitzgerald</author>
    #                 </book>
    #                 <book>
    #                     <title>To Kill a Mockingbird</title>
    #                     <author>Harper Lee</author>
    #                 </book>
    #             </library>
    #     """
    #     new_elements = [
    #         NewElement(name="child2", parent_name="root"),
    #         NewElement(name="child3", parent_name="root", content="3", attributes={"one": "1"})
    #     ]
    #     self.run_and_assert(new_elements, input_code, expected_output)

    # def test_add_new_sibling_element(self):
    #     input_code = """\
    #             <root>
    #                 <child1>Content 1</child1>
    #             </root>
    #     """
    #     expected_output = """\
    #             <?xml version="1.0" encoding="utf-8"?>
    #             <root>
    #                 <child1>Content 1</child1>
    #                 <child2></child2>
    #                 <child3 one="1">3</child3>
    #             </root>
    #     """
    #     new_elements = [
    #         NewElement(name="child2", parent_name="root"),
    #         NewElement(name="child3", parent_name="root", content="3", attributes={"one": "1"})
    #     ]
    #     self.run_and_assert(new_elements, input_code, expected_output)
