from collections import namedtuple

import libcst as cst
from libcst import matchers
from libcst._position import CodeRange
from libcst.codemod import CodemodContext
from libcst.metadata import PositionProvider
from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor

from codemodder.change import Change, ChangeSet
from codemodder.codemods.base_transformer import BaseTransformerPipeline
from codemodder.codemods.base_visitor import BaseTransformer
from codemodder.codemods.utils import get_call_name
from codemodder.context import CodemodExecutionContext
from codemodder.dependency import Dependency
from codemodder.diff import create_diff_from_tree
from codemodder.file_context import FileContext
from codemodder.logging import logger
from codemodder.result import Result

NewArg = namedtuple("NewArg", ["name", "value", "add_if_missing"])


def update_code(file_path, new_code):
    """
    Write the `new_code` to the `file_path`
    """
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_code)


class LibcstResultTransformer(BaseTransformer):
    """
    Transformer class that performs libcst-based transformations on a given file

    :param context: libcst CodemodContext
    :param results: list of `Result` generated by the detector phase (may be empty)
    :param file_context: `FileContext` for the file to be transformed
    """

    change_description: str = ""

    def __init__(
        self,
        context: CodemodContext,
        results: list[Result] | None,
        file_context: FileContext,
        _transformer: bool = False,
    ):
        del _transformer

        self.file_context = file_context
        super().__init__(
            context,
            results,
            line_include=file_context.line_include,
            line_exclude=file_context.line_exclude,
        )

    @classmethod
    def transform(
        cls, module: cst.Module, results: list[Result] | None, file_context: FileContext
    ) -> cst.Module:
        wrapper = cst.MetadataWrapper(module)
        codemod = cls(
            CodemodContext(wrapper=wrapper),
            results,
            file_context,
            _transformer=True,
        )

        return codemod.transform_module(module)

    def _new_or_updated_node(self, original_node, updated_node):
        if self.node_is_selected(original_node):
            if (attr := getattr(self, "on_result_found", None)) is not None:
                new_node = attr(original_node, updated_node)
                self.report_change(original_node)
                return new_node
        return updated_node

    # TODO: there needs to be a way to generalize this so that it applies
    # more broadly than to just a specific kind of node. There's probably a
    # decent way to do this with metaprogramming. We could either apply it
    # broadly to every known method (which would probably have a big
    # performance impact). Or we could allow users to register the handler
    # for a specific node or nodes by means of a decorator or something
    # similar when they define their `on_result_found` method.
    # Right now this is just to demonstrate a particular use case.
    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call):
        return self._new_or_updated_node(original_node, updated_node)

    def leave_Assign(self, original_node, updated_node):
        return self._new_or_updated_node(original_node, updated_node)

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.ClassDef:
        return self._new_or_updated_node(original_node, updated_node)

    def node_position(self, node):
        # See https://github.com/Instagram/LibCST/blob/main/libcst/_metadata_dependent.py#L112
        return self.get_metadata(PositionProvider, node)

    def add_change(self, node, description: str, start: bool = True):
        position = self.node_position(node)
        self.add_change_from_position(position, description, start)

    def add_change_from_position(
        self, position: CodeRange, description: str, start: bool = True
    ):
        lineno = position.start.line if start else position.end.line
        self.file_context.codemod_changes.append(
            Change(
                lineNumber=lineno,
                description=description,
            )
        )

    def lineno_for_node(self, node):
        return self.node_position(node).start.line

    def add_dependency(self, dependency: Dependency):
        self.file_context.add_dependency(dependency)

    def report_change(self, original_node):
        line_number = self.lineno_for_node(original_node)
        self.file_context.codemod_changes.append(
            Change(line_number, self.change_description)
        )

    def remove_unused_import(self, original_node):
        RemoveImportsVisitor.remove_unused_import_by_node(self.context, original_node)

    def add_needed_import(self, module, obj=None):
        # TODO: do we need to check if this import already exists?
        AddImportsVisitor.add_needed_import(self.context, module, obj)

    def update_call_target(
        self,
        original_node,
        new_target,
        new_func: str | None = None,
        replacement_args=None,
    ):
        # TODO: is an assertion the best way to handle this?
        # Or should we just return the original node if it's not a Call?
        assert isinstance(original_node, cst.Call)

        func_name = new_func if new_func else get_call_name(original_node)
        return cst.Call(
            func=cst.Attribute(
                value=cst.parse_expression(new_target),
                attr=cst.Name(value=func_name),
            ),
            args=replacement_args if replacement_args else original_node.args,
        )

    def update_arg_target(self, updated_node, new_args: list):
        return updated_node.with_changes(
            args=[new if isinstance(new, cst.Arg) else cst.Arg(new) for new in new_args]
        )

    def update_assign_rhs(self, updated_node: cst.Assign, rhs: str):
        value = cst.parse_expression(rhs)
        return updated_node.with_changes(value=value)

    def parse_expression(self, expression: str):
        return cst.parse_expression(expression)

    def replace_args(self, original_node, args_info):
        """
        Iterate over the args in original_node and replace each arg
        with any matching arg in `args_info`.

        :param original_node: libcst node with args attribute.
        :param list args_info: List of NewArg
        """
        assert hasattr(original_node, "args")
        assert all(
            isinstance(arg, NewArg) for arg in args_info
        ), "`args_info` must contain `NewArg` types."
        new_args = []

        for arg in original_node.args:
            arg_name, replacement_val, idx = _match_with_existing_arg(arg, args_info)
            if arg_name is not None:
                new = self.make_new_arg(replacement_val, arg_name, arg)
                del args_info[idx]
            else:
                new = arg
            new_args.append(new)

        for arg_name, replacement_val, add_if_missing in args_info:
            if add_if_missing:
                new = self.make_new_arg(replacement_val, arg_name)
                new_args.append(new)

        return new_args

    def make_new_arg(self, value, name=None, existing_arg=None):
        if name is None:
            # Make a positional argument
            return cst.Arg(
                value=cst.parse_expression(value),
            )

        # make a keyword argument
        equal = (
            existing_arg.equal
            if existing_arg
            else cst.AssignEqual(
                whitespace_before=cst.SimpleWhitespace(""),
                whitespace_after=cst.SimpleWhitespace(""),
            )
        )
        return cst.Arg(
            keyword=cst.Name(value=name),
            value=cst.parse_expression(value),
            equal=equal,
        )

    def add_arg_to_call(self, node: cst.Call, name: str, value):
        """
        Add a new arg to the end of the args list.
        """
        new_args = list(node.args) + [
            cst.Arg(
                keyword=cst.Name(value=name),
                value=cst.parse_expression(str(value)),
                equal=cst.AssignEqual(
                    whitespace_before=cst.SimpleWhitespace(""),
                    whitespace_after=cst.SimpleWhitespace(""),
                ),
            )
        ]
        return node.with_changes(args=new_args)


class LibcstTransformerPipeline(BaseTransformerPipeline):
    """
    Transformer pipeline class that applies one or more `LibcstResultTransformer` to a given file

    This pipeline expects that all transformers accept a libcst `Module` as input and return a libcst `Module` as output.
    """

    transformers: list[type[LibcstResultTransformer]]

    def apply(
        self,
        context: CodemodExecutionContext,
        file_context: FileContext,
        results: list[Result] | None,
    ) -> ChangeSet | None:
        file_path = file_context.file_path

        try:
            with file_context.timer.measure("parse"):
                with open(file_path, "r", encoding="utf-8") as f:
                    source_tree = cst.parse_module(f.read())
        except Exception:
            file_context.add_failure(file_path)
            logger.exception("error parsing file %s", file_path)
            return None

        tree = source_tree
        with file_context.timer.measure("transform"):
            for transformer in self.transformers:
                tree = transformer.transform(tree, results, file_context)

        if not file_context.codemod_changes:
            return None

        diff = create_diff_from_tree(source_tree, tree)
        if not diff:
            return None

        change_set = ChangeSet(
            str(file_context.file_path.relative_to(context.directory)),
            diff,
            changes=file_context.codemod_changes,
        )

        if not context.dry_run:
            with file_context.timer.measure("write"):
                update_code(file_context.file_path, tree.code)

        return change_set


def _match_with_existing_arg(arg, args_info):
    """
    Given an `arg` and a list of arg info, determine if any of the names in arg_info match the arg.
    """
    for idx, (arg_name, replacement_val, _) in enumerate(args_info):
        if matchers.matches(arg.keyword, matchers.Name(arg_name)):
            return arg_name, replacement_val, idx
    return None, None, None
