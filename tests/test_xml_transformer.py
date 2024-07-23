from io import StringIO
from textwrap import dedent
from xml.sax import handler

import mock
import pytest
from defusedxml import ExternalReferenceForbidden
from defusedxml.sax import make_parser

from codemodder.codemods.xml_transformer import (
    ElementAttributeXMLTransformer,
    NewElement,
    NewElementXMLTransformer,
    XMLTransformer,
)
from codemodder.semgrep import SemgrepResult


class TestXMLTransformer:

    def run_and_assert(self, input_code, expected_output):
        with StringIO() as result, StringIO(dedent(input_code)) as input_stream:
            result = StringIO()
            transformer = XMLTransformer(result, mock.MagicMock())
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

    def run_and_assert(
        self,
        name_attr_map,
        input_code,
        expected_output,
        results=None,
        line_only_match=False,
    ):
        with StringIO() as result, StringIO(dedent(input_code)) as input_stream:
            transformer = ElementAttributeXMLTransformer(
                result,
                mock.MagicMock(),
                name_attributes_map=name_attr_map,
                results=results,
                line_only_matching=line_only_match,
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

    def test_change_only_line_matching_result(self):
        input_code = """\
        <?xml version="1.0" encoding="utf-8"?>
        <configuration>
          <element first="1">
          </element>
          <element first="1">
          </element>
        </configuration>"""
        expected_output = """\
        <?xml version="1.0" encoding="utf-8"?>
        <configuration>
          <element first="1">
          </element>
          <element first="one">
          </element>
        </configuration>"""
        name_attr_map = {"element": {"first": "one"}}
        data = {
            "runs": [
                {
                    "results": [
                        {
                            "fingerprints": {"matchBasedId/v1": "123"},
                            "locations": [
                                {
                                    "ruleId": "rule",
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": "code.py",
                                            "uriBaseId": "%SRCROOT%",
                                        },
                                        "region": {
                                            "snippet": {"text": "snip"},
                                            "endColumn": 1,
                                            "endLine": 5,
                                            "startColumn": 1,
                                            "startLine": 5,
                                        },
                                    },
                                }
                            ],
                            "ruleId": "rule",
                        }
                    ]
                }
            ]
        }
        sarif_run = data["runs"]
        sarif_results = sarif_run[0]["results"]
        results = [SemgrepResult.from_sarif(sarif_results[0], sarif_run)]
        self.run_and_assert(name_attr_map, input_code, expected_output, results, True)


class TestNewElementXMLTransformer:

    def run_and_assert(self, new_elements, input_code, expected_output):
        with StringIO() as result, StringIO(dedent(input_code)) as input_stream:
            transformer = NewElementXMLTransformer(
                result, mock.MagicMock(), new_elements=new_elements
            )
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

    def test_add_nested_elementsl(self):
        input_code = """\
        <?xml version="1.0" encoding="utf-8" ?>
        <configuration>
          <system.web>
          </system.web>
          <system.webServer>
            <validation validateIntegratedModeConfiguration="false" />
            <modules>
              <remove name="ScriptModule" />
              <add name="ScriptModule" preCondition="managedHandler" type="System.Web.Handlers.ScriptModule, System.Web.Extensions, Version=3.5.0.0, Culture=neutral, PublicKeyToken=31BF3856AD364E35" />
            </modules>
          </system.webServer>
        </configuration>
        """
        expected_output = """\
        <?xml version="1.0" encoding="utf-8"?>
        <configuration>
          <system.web>
          </system.web>
          <system.webServer>
            <validation validateIntegratedModeConfiguration="false"></validation>
            <modules>
              <remove name="ScriptModule"></remove>
              <add name="ScriptModule" preCondition="managedHandler" type="System.Web.Handlers.ScriptModule, System.Web.Extensions, Version=3.5.0.0, Culture=neutral, PublicKeyToken=31BF3856AD364E35"></add>
            </modules>
          <httpProtocol><customHeaders><add name="X-Frame-Options" value="DENY"></add></customHeaders></httpProtocol></system.webServer>
        </configuration>"""
        new_elements = [
            NewElement(
                name="httpProtocol",
                parent_name="system.webServer",
                content=NewElement(
                    name="customHeaders",
                    parent_name="httpProtocol",
                    content=NewElement(
                        name="add",
                        parent_name="customHeaders",
                        attributes={"name": "X-Frame-Options", "value": "DENY"},
                    ),
                ),
            ),
        ]
        self.run_and_assert(new_elements, input_code, expected_output)
