import pytest

from core_codemods.use_defused_xml import (
    DOM_METHODS,
    ETREE_METHODS,
    SAX_METHODS,
    UseDefusedXml,
)
from tests.codemods.base_codemod_test import BaseCodemodTest


class TestUseDefusedXml(BaseCodemodTest):
    codemod = UseDefusedXml

    @pytest.mark.parametrize("method", ETREE_METHODS)
    @pytest.mark.parametrize("module", ["ElementTree", "cElementTree"])
    def test_etree_simple_call(self, tmpdir, module, method):
        original_code = f"""
            from xml.etree.{module} import {method}, ElementPath

            et = {method}('some.xml')
        """

        new_code = f"""
            from xml.etree.{module} import ElementPath
            import defusedxml.ElementTree

            et = defusedxml.ElementTree.{method}('some.xml')
        """

        self.run_and_assert(tmpdir, original_code, new_code)

    @pytest.mark.parametrize("method", ETREE_METHODS)
    @pytest.mark.parametrize("module", ["ElementTree", "cElementTree"])
    def test_etree_attribute_call(self, tmpdir, module, method):
        original_code = f"""
            from xml.etree import {module}

            et = {module}.{method}('some.xml')
        """

        new_code = f"""
            import defusedxml.ElementTree

            et = defusedxml.ElementTree.{method}('some.xml')
        """

        self.run_and_assert(tmpdir, original_code, new_code)

    def test_etree_elementtree_with_alias(self, tmpdir):
        original_code = """
            from xml.etree import ElementTree as ET

            et = ET.parse('some.xml')
        """

        new_code = """
            import defusedxml.ElementTree

            et = defusedxml.ElementTree.parse('some.xml')
        """

        self.run_and_assert(tmpdir, original_code, new_code)

    def test_etree_parse_with_alias(self, tmpdir):
        original_code = """
            from xml.etree.ElementTree import parse as parse_xml

            et = parse_xml('some.xml')
        """

        new_code = """
            import defusedxml.ElementTree

            et = defusedxml.ElementTree.parse('some.xml')
        """

        self.run_and_assert(tmpdir, original_code, new_code)

    @pytest.mark.parametrize("method", SAX_METHODS)
    def test_sax_simple_call(self, tmpdir, method):
        original_code = f"""
            from xml.sax import {method}

            et = {method}('some.xml')
        """

        new_code = f"""
            import defusedxml.sax

            et = defusedxml.sax.{method}('some.xml')
        """

        self.run_and_assert(tmpdir, original_code, new_code)

    @pytest.mark.parametrize("method", SAX_METHODS)
    def test_sax_attribute_call(self, tmpdir, method):
        original_code = f"""
            from xml import sax

            et = sax.{method}('some.xml')
        """

        new_code = f"""
            import defusedxml.sax

            et = defusedxml.sax.{method}('some.xml')
        """

        self.run_and_assert(tmpdir, original_code, new_code)

    @pytest.mark.parametrize("method", DOM_METHODS)
    @pytest.mark.parametrize("module", ["minidom", "pulldom"])
    def test_dom_simple_call(self, tmpdir, module, method):
        original_code = f"""
            from xml.dom.{module} import {method}

            et = {method}('some.xml')
        """

        new_code = f"""
            import defusedxml.{module}

            et = defusedxml.{module}.{method}('some.xml')
        """

        self.run_and_assert(tmpdir, original_code, new_code)
