from collections import defaultdict

import libcst as cst
from libcst.codemod import CodemodContext
from libcst.metadata import PositionProvider
from codemodder.codemods.base_visitor import BaseTransformer


class DeleteStatementLinesCodemod(BaseTransformer):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, context, results, line_exclude=None, line_include=None):
        BaseTransformer.__init__(self, context, results)
        self.line_exclude = line_exclude or []
        self.line_include = line_include or []

    def filter_by_result(self, pos_to_match):
        return True

    def leave_SimpleStatementLine(
        self, original_node: cst.SimpleStatementLine, updated_node
    ):
        pos_to_match = self.node_position(original_node)
        if self.filter_by_result(
            pos_to_match
        ) and self.filter_by_path_includes_or_excludes(pos_to_match):
            return cst.RemovalSentinel.REMOVE
        return original_node


class TestBaseVisitor:
    def run_and_assert(self, input_code, expected, line_exclude, line_include):
        input_tree = cst.parse_module(input_code)
        command_instance = DeleteStatementLinesCodemod(
            CodemodContext(), defaultdict(list), line_exclude, line_include
        )
        output_tree = command_instance.transform_module(input_tree)

        assert output_tree.code == expected

    def test_excludes(self):
        input_code = """print('Hello Earth')\nprint('Hello Mars')"""
        expected = """print('Hello Earth')"""
        line_exclude = [1]
        line_include = []
        self.run_and_assert(input_code, expected, line_exclude, line_include)

    def test_includes(self):
        input_code = """print('Hello Earth')\nprint('Hello Mars')"""
        expected = """print('Hello Mars')"""
        line_exclude = []
        line_include = [1]
        self.run_and_assert(input_code, expected, line_exclude, line_include)

    def test_includes_excludes(self):
        input_code = """print('Hello Earth')\nprint('Hello Mars')"""
        expected = """print('Hello Earth')"""
        line_exclude = [1]
        line_include = [1]
        self.run_and_assert(input_code, expected, line_exclude, line_include)
