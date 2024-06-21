import pytest

from codemodder.codemods.test import BaseCodemodTest
from core_codemods.lxml_safe_parser_defaults import LxmlSafeParserDefaults

each_class = pytest.mark.parametrize(
    "klass", ["XMLParser", "ETCompatXMLParser", "XMLTreeBuilder", "XMLPullParser"]
)


class TestLxmlSafeParserDefaults(BaseCodemodTest):
    codemod = LxmlSafeParserDefaults

    def test_name(self):
        assert self.codemod.name == "safe-lxml-parser-defaults"

    @each_class
    def test_import(self, tmpdir, klass):
        input_code = f"""import lxml.etree

parser = lxml.etree.{klass}()
var = "hello"
"""
        expexted_output = f"""import lxml.etree

parser = lxml.etree.{klass}(resolve_entities=False)
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expexted_output)

    @each_class
    def test_from_import(self, tmpdir, klass):
        input_code = f"""from lxml.etree import {klass}

parser = {klass}()
var = "hello"
"""
        expexted_output = f"""from lxml.etree import {klass}

parser = {klass}(resolve_entities=False)
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expexted_output)

    @each_class
    def test_from_import_module(self, tmpdir, klass):
        input_code = f"""from lxml import etree

parser = etree.{klass}()
var = "hello"
"""
        expexted_output = f"""from lxml import etree

parser = etree.{klass}(resolve_entities=False)
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expexted_output)

    @each_class
    def test_import_alias(self, tmpdir, klass):
        input_code = f"""from lxml.etree import {klass} as xmlklass

parser = xmlklass()
var = "hello"
"""
        expexted_output = f"""from lxml.etree import {klass} as xmlklass

parser = xmlklass(resolve_entities=False)
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expexted_output)

    @pytest.mark.parametrize(
        "input_args,expected_args",
        [
            (
                "resolve_entities=True",
                "resolve_entities=False",
            ),
            (
                "resolve_entities=False",
                "resolve_entities=False",
            ),
            (
                """resolve_entities=True, no_network=False, dtd_validation=True""",
                """resolve_entities=False, no_network=True, dtd_validation=False""",
            ),
            (
                """dtd_validation=True""",
                """dtd_validation=False, resolve_entities=False""",
            ),
            (
                """no_network=False""",
                """no_network=True, resolve_entities=False""",
            ),
            (
                """no_network=True""",
                """no_network=True, resolve_entities=False""",
            ),
        ],
    )
    @each_class
    def test_verify_variations(self, tmpdir, klass, input_args, expected_args):
        input_code = f"""import lxml.etree
parser = lxml.etree.{klass}({input_args})
var = "hello"
"""
        expexted_output = f"""import lxml.etree
parser = lxml.etree.{klass}({expected_args})
var = "hello"
"""
        self.run_and_assert(tmpdir, input_code, expexted_output)
