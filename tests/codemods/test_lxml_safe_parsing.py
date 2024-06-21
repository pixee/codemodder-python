import pytest

from codemodder.codemods.test import BaseCodemodTest
from core_codemods.lxml_safe_parsing import LxmlSafeParsing

each_func = pytest.mark.parametrize("func", ["parse", "fromstring"])


class TestLxmlSafeParsing(BaseCodemodTest):
    codemod = LxmlSafeParsing

    def test_name(self):
        assert self.codemod.name == "safe-lxml-parsing"

    @each_func
    def test_import(self, tmpdir, func):
        input_code = f"""import lxml.etree

lxml.etree.{func}("path_to_file")
var = "hello"
"""
        expexted_output = f"""import lxml.etree

lxml.etree.{func}("path_to_file", parser=lxml.etree.XMLParser(resolve_entities=False))
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expexted_output)

    @each_func
    def test_from_import(self, tmpdir, func):
        input_code = f"""from lxml.etree import {func}

{func}("path_to_file")
var = "hello"
"""
        expexted_output = f"""from lxml.etree import {func}
import lxml.etree

{func}("path_to_file", parser=lxml.etree.XMLParser(resolve_entities=False))
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expexted_output)

    @each_func
    def test_from_import_module(self, tmpdir, func):
        input_code = f"""from lxml import etree

etree.{func}("path_to_file")
var = "hello"
"""
        expexted_output = f"""from lxml import etree
import lxml.etree

etree.{func}("path_to_file", parser=lxml.etree.XMLParser(resolve_entities=False))
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expexted_output)

    @each_func
    def test_import_alias(self, tmpdir, func):
        input_code = f"""from lxml.etree import {func} as func

func("path_to_file")
var = "hello"
"""
        expexted_output = f"""from lxml.etree import {func} as func
import lxml.etree

func("path_to_file", parser=lxml.etree.XMLParser(resolve_entities=False))
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expexted_output)

    @pytest.mark.parametrize(
        "input_args,expected_args",
        [
            (
                "'str', parser=None",
                "'str', parser=lxml.etree.XMLParser(resolve_entities=False)",
            ),
            (
                "source, base_url='url', parser=None",
                "source, base_url='url', parser=lxml.etree.XMLParser(resolve_entities=False)",
            ),
            (
                "source, parser=lxml.etree.XMLParser(resolve_entities=False)",
                "source, parser=lxml.etree.XMLParser(resolve_entities=False)",
            ),
            # This case would be changed by `safe-lxml-parser-defaults` codemod
            (
                "source, parser=lxml.etree.XMLParser()",
                "source, parser=lxml.etree.XMLParser()",
            ),
        ],
    )
    @each_func
    def test_verify_variations(self, tmpdir, func, input_args, expected_args):
        input_code = f"""import lxml.etree
lxml.etree.{func}({input_args})
var = "hello"
"""
        expexted_output = f"""import lxml.etree
lxml.etree.{func}({expected_args})
var = "hello"
"""
        self.run_and_assert(tmpdir, input_code, expexted_output)
