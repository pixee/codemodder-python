from collections import defaultdict
from textwrap import dedent

import libcst as cst
from libcst._position import CodePosition, CodeRange
from libcst.codemod import CodemodContext
from libcst.metadata import PositionProvider

from codemodder.codemods.base_visitor import BaseTransformer


class DeleteStatementLinesCodemod(BaseTransformer):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, context, results, line_exclude=None, line_include=None):
        BaseTransformer.__init__(
            self, context, results, line_include or [], line_exclude or []
        )

    def filter_by_result(self, node):
        return True

    def leave_SimpleStatementLine(
        self, original_node: cst.SimpleStatementLine, updated_node
    ):
        pos_to_match = self.node_position(original_node)
        if self.filter_by_result(
            original_node
        ) and self.filter_by_path_includes_or_excludes(pos_to_match):
            return cst.RemovalSentinel.REMOVE
        return original_node


class AssertPositionCodemod(BaseTransformer):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(
        self,
        context,
        results,
        expected_node_position,
        line_exclude=None,
        line_include=None,
    ):
        BaseTransformer.__init__(
            self, context, results, line_include or [], line_exclude or []
        )
        self.expected_node_position = expected_node_position

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        pos_to_match = self.node_position(original_node)
        assert pos_to_match == self.expected_node_position
        return updated_node


class AssertNodeCode(BaseTransformer):
    def __init__(
        self,
        context,
        results,
        expected_code,
        node_type,
        line_exclude=None,
        line_include=None,
    ):
        BaseTransformer.__init__(
            self, context, results, line_include or [], line_exclude or []
        )
        self.expected_code = expected_code
        self.node_type = node_type
        self.checked = False

    def on_leave(
        self, original_node: cst.CSTNode, updated_node: cst.CSTNode
    ) -> cst.CSTNode:
        match original_node:
            case self.node_type():
                assert self.code(original_node).strip() == self.expected_code.strip()
                self.checked = True

        return updated_node


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


class TestNodePosition:
    def run_and_assert(self, input_code, expected_pos):
        input_tree = cst.parse_module(dedent(input_code))
        command_instance = AssertPositionCodemod(
            CodemodContext(), defaultdict(list), expected_pos
        )
        command_instance.transform_module(input_tree)

    def test_funcdef(self):
        input_code = """
        def hello():
            pass
        """
        expected_pos = CodeRange(
            start=CodePosition(line=2, column=0), end=CodePosition(line=2, column=11)
        )
        self.run_and_assert(input_code, expected_pos)

    def test_instance(self):
        input_code = """
        class MyClass:
            def instance_method():
                print("instance_method")
        """
        expected_pos = CodeRange(
            start=CodePosition(line=3, column=4), end=CodePosition(line=3, column=25)
        )
        self.run_and_assert(input_code, expected_pos)

    def test_funcdef_args(self):
        input_code = """
        def hello(one, *args, **kwargs):
            pass
        """
        expected_pos = CodeRange(
            start=CodePosition(line=2, column=0), end=CodePosition(line=2, column=31)
        )
        self.run_and_assert(input_code, expected_pos)


class TestCodeForNode:
    def run_and_assert(self, input_code, expected_code, node_type):
        input_tree = cst.parse_module(dedent(input_code))
        command_instance = AssertNodeCode(
            CodemodContext(), defaultdict(list), expected_code, node_type
        )
        command_instance.transform_module(input_tree)
        if not command_instance.checked:
            raise Exception(f"Input code does not contain a {node_type}")

    def test_annAssign(self):
        input_code = "phones: list = [1, 2, 3]"
        self.run_and_assert(input_code, input_code, cst.AnnAssign)

    def test_list(self):
        input_code = "[1, 'two', Exception]"
        self.run_and_assert(input_code, input_code, cst.List)

    def test_dict(self):
        self.run_and_assert('dict = {"friend": "one"}', '{"friend": "one"}', cst.Dict)

    def test_module(self):
        input_code = dedent(
            """
        # comment
        var = 1
        print(var)
        """
        )
        self.run_and_assert(input_code, input_code, cst.Module)
