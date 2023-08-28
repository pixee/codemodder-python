import libcst as cst
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

    def update_call_target(self, original_node, new_target, replacement_args=None):
        # TODO: is an assertion the best way to handle this?
        # Or should we just return the original node if it's not a Call?
        assert isinstance(original_node, cst.Call)
        return cst.Call(
            func=cst.Attribute(
                value=cst.parse_expression(new_target),
                attr=cst.Name(value=get_call_name(original_node)),
            ),
            args=replacement_args if replacement_args else original_node.args,
        )

    def update_arg_target(self, updated_node, new_arg):
        return updated_node.with_changes(args=[cst.Arg(new_arg)])
