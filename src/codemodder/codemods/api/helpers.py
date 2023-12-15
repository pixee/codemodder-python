from collections import namedtuple
import libcst as cst
from libcst import matchers
from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor
from codemodder.codemods.utils import get_call_name

NewArg = namedtuple("NewArg", ["name", "value", "add_if_missing"])


class Helpers:
    def remove_unused_import(self, original_node):
        # pylint: disable=no-member
        RemoveImportsVisitor.remove_unused_import_by_node(self.context, original_node)

    def add_needed_import(self, module, obj=None):
        # TODO: do we need to check if this import already exists?
        AddImportsVisitor.add_needed_import(
            self.context, module, obj  # pylint: disable=no-member
        )

    def update_call_target(
        self, original_node, new_target, new_func=None, replacement_args=None
    ):
        # TODO: is an assertion the best way to handle this?
        # Or should we just return the original node if it's not a Call?
        assert isinstance(original_node, cst.Call)

        attr = (
            cst.parse_expression(new_func)
            if new_func
            else cst.Name(value=get_call_name(original_node))
        )
        return cst.Call(
            func=cst.Attribute(
                value=cst.parse_expression(new_target),
                attr=attr,
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


def _match_with_existing_arg(arg, args_info):
    """
    Given an `arg` and a list of arg info, determine if
    any of the names in arg_info match the arg.
    """
    for idx, (arg_name, replacement_val, _) in enumerate(args_info):
        if matchers.matches(arg.keyword, matchers.Name(arg_name)):
            return arg_name, replacement_val, idx
    return None, None, None
