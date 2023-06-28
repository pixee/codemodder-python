from collections import defaultdict
from typing import DefaultDict
import libcst as cst
from libcst.codemod import Codemod, CodemodContext
import pytest
from codemodder.codemods.base_codemod import BaseCodemod


class DoNothingCodemod(BaseCodemod, Codemod):
    NAME = "do-nothing"
    DESCRIPTION = "An identity codemod for testing purposes."
    RULE_IDS = []

    def __init__(self, context: CodemodContext, results_by_id):
        Codemod.__init__(self, context)
        BaseCodemod.__init__(self, results_by_id)

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        return tree


class TestEmptyResults:
    RESULTS_BY_ID: DefaultDict = defaultdict()

    def run_and_assert(self, input_code, expexted_output):
        input_tree = cst.parse_module(input_code)
        command_instance = DoNothingCodemod(CodemodContext(), self.RESULTS_BY_ID)
        output_tree = command_instance.transform_module(input_tree)

        assert output_tree.code == expexted_output

    def test_empty_results(self):
        input_code = """print('Hello World')"""
        self.run_and_assert(input_code, input_code)


class TestBaseCodemod:
    def test_missing_class_attrs(self):
        with pytest.raises(NotImplementedError):

            class MissingInfoCodemod(BaseCodemod):
                ...

        with pytest.raises(NotImplementedError):

            class MissingInfoCodemod(BaseCodemod):
                NAME = "something"

        with pytest.raises(NotImplementedError):

            class MissingInfoCodemod(BaseCodemod):
                NAME = "something"
                DESCRIPTION = "something else"
