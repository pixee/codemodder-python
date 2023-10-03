import libcst as cst
from libcst import matchers
from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor
from codemodder.codemods.utils import get_call_name


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

    def replace_args(
        self,
        original_node,
        args_info,
    ):
        new_args = []

        for arg in original_node.args:
            arg_name, replacement_val, idx = _match_with_existing_arg(arg, args_info)
            if arg_name is not None:
                new = self.make_new_arg(arg_name, replacement_val, arg)
                del args_info[idx]
            else:
                new = arg
            new_args.append(new)

        for arg_name, replacement_val, add_if_missing in args_info:
            if add_if_missing:
                new = self.make_new_arg(arg_name, replacement_val)
                new_args.append(new)

        return new_args

    def replace_arg(
        self,
        original_node,
        target_arg_name,
        target_arg_replacement_val,
        add_if_missing=False,
    ):
        """Given a node, return its args with one arg's value changed.

        If add_if_missing is True, then if target arg is not present, add it.
        """
        assert hasattr(original_node, "args")
        new_args = []
        arg_added = False

        for arg in original_node.args:
            if matchers.matches(arg.keyword, matchers.Name(target_arg_name)):
                new = self.make_new_arg(
                    target_arg_name, target_arg_replacement_val, arg
                )
                arg_added = True
            else:
                new = arg
            new_args.append(new)

        if add_if_missing and not arg_added:
            new = self.make_new_arg(target_arg_name, target_arg_replacement_val)
            new_args.append(new)
        return new_args

    def make_new_arg(self, name, value, existing_arg=None):
        equal = (
            existing_arg.equal
            if existing_arg
            else cst.AssignEqual(
                whitespace_before=cst.SimpleWhitespace(""),
                whitespace_after=cst.SimpleWhitespace(""),
            )
        )
        return cst.Arg(
            keyword=cst.parse_expression(name),
            value=cst.parse_expression(value),
            equal=equal,
        )


def _match_with_existing_arg(arg, args_info):
    """
    Given an `arg` and a list of arg info, determine if
    any of the names in arg_info match the arg.
    """
    for idx, (arg_name, replacement_val, add_if_missing) in enumerate(args_info):
        if matchers.matches(arg.keyword, matchers.Name(arg_name)):
            return arg_name, replacement_val, idx
    return None, None, None
