from ast import literal_eval
from typing import Union

import libcst as cst
import libcst.matchers as matchers
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand
from libcst.codemod.visitors import AddImportsVisitor


class SecureRandom(VisitorBasedCodemodCommand):

    # Add a description so that future codemodders can see what this does.
    DESCRIPTION: str = "Replaces random.random with secrets."

    def __init__(
        self, context: CodemodContext
    ):  # , string: str, constant: str) -> None:
        # Initialize the base class with context, and save our args. Remember, the
        # "dest" for each argument we added above must match a parameter name in
        # this init.
        super().__init__(context)
        # self.string = string
        # self.constant = constant

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        if is_random_node(original_node):
            weave = cst.parse_expression("shlex.split(arg0)")
            weave = weave.with_changes(
                args=[weave.args[0].with_changes(value=updated_node.args)]
            )
            return updated_node.with_changes(
                args=[updated_node.args, *updated_node.args[1:]]
            )
        return updated_node


def is_random_node(node: cst.Call) -> bool:
    # todo: test against custom random functions
    return matchers.matches(
        node,
        matchers.Call(func=matchers.Attribute(value=matchers.Name(value="random"))),
    )
