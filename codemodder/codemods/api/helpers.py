import libcst as cst
from libcst.codemod.visitors import AddImportsVisitor

from codemodder.codemods.utils import get_call_name


class Helpers:
    def add_needed_import(self, import_name):
        # TODO: do we need to check if this import already exists?
        AddImportsVisitor.add_needed_import(self.context, import_name)

    def update_call_target(self, original_node, new_target):
        # TODO: is an assertion the best way to handle this?
        # Or should we just return the original node if it's not a Call?
        assert isinstance(original_node, cst.Call)
        return cst.Call(
            func=cst.Attribute(
                value=cst.parse_expression(new_target),
                attr=cst.Name(value=get_call_name(original_node)),
            ),
            args=original_node.args,
        )
