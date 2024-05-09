from enum import Enum
from pathlib import Path
from typing import Any, Optional, TypeAlias

import libcst as cst
from libcst import MetadataDependent, matchers
from libcst.codemod import CodemodContext
from libcst.matchers import MatcherDecoratableTransformer


class BaseType(Enum):
    """
    An enumeration representing the base literal types in Python.
    """

    NUMBER = 1
    LIST = 2
    STRING = 3
    BYTES = 4
    NONE = 5
    TRUE = 6
    FALSE = 7


def infer_expression_type(node: cst.BaseExpression) -> Optional[BaseType]:
    """
    Tries to infer if the resulting type of a given expression is one of the base literal types.
    """
    # The current implementation covers some common cases and is in no way complete
    match node:
        case cst.Name(value="None"):
            return BaseType.NONE
        case cst.Name(value="True"):
            return BaseType.TRUE
        case cst.Name(value="False"):
            return BaseType.FALSE
        case (
            cst.Integer()
            | cst.Imaginary()
            | cst.Float()
            | cst.Call(func=cst.Name("int"))
            | cst.Call(func=cst.Name("float"))
            | cst.Call(func=cst.Name("abs"))
            | cst.Call(func=cst.Name("len"))
        ):
            return BaseType.NUMBER
        case cst.Call(name=cst.Name("list")) | cst.List() | cst.ListComp():
            return BaseType.LIST
        case cst.Call(func=cst.Name("str")) | cst.FormattedString():
            return BaseType.STRING
        case cst.SimpleString():
            if "b" in node.prefix.lower():
                return BaseType.BYTES
            return BaseType.STRING
        case cst.ConcatenatedString():
            return infer_expression_type(node.left)
        case cst.BinaryOperation(operator=cst.Add()):
            return infer_expression_type(node.left) or infer_expression_type(node.right)
        case cst.BinaryOperation(operator=cst.Modulo()):
            return infer_expression_type(node.left) or infer_expression_type(node.right)
        case cst.IfExp():
            if_true = infer_expression_type(node.body)
            or_else = infer_expression_type(node.orelse)
            if if_true == or_else:
                return if_true
    return None


class SequenceExtension:
    def __init__(self, sequence: list[cst.CSTNode]) -> None:
        self.sequence = sequence


class Append(SequenceExtension):
    pass


class Prepend(SequenceExtension):
    pass


ReplacementNodeType: TypeAlias = (
    cst.CSTNode | cst.RemovalSentinel | cst.FlattenSentinel | dict[str, Any]
)


class ReplaceNodes(cst.CSTTransformer):
    """
    Replace nodes with their corresponding values in a given dict. The replacements dictionary should either contain a mapping from a node to another node, RemovalSentinel, or FlattenSentinel to be replaced, or a dict mapping each attribute, by name, to a new value. Additionally if the attribute is a sequence, you may pass Append(l)/Prepend(l), where l is a list of nodes, to append or prepend, respectively.
    """

    def __init__(
        self,
        replacements: dict[
            cst.CSTNode,
            ReplacementNodeType | dict[str, Any],
        ],
    ):
        self.replacements = replacements

    def on_leave(self, original_node, updated_node):
        if original_node in self.replacements.keys():
            replacement = self.replacements[original_node]
            match replacement:
                case dict():
                    changes_dict = {}
                    for key, value in replacement.items():
                        match value:
                            case Prepend():
                                changes_dict[key] = value.sequence + [
                                    *getattr(updated_node, key)
                                ]

                            case Append():
                                changes_dict[key] = [
                                    *getattr(updated_node, key)
                                ] + value.sequence
                            case _:
                                changes_dict[key] = value
                    return updated_node.with_changes(**changes_dict)
                case cst.CSTNode() | cst.RemovalSentinel() | cst.FlattenSentinel():
                    return replacement
        return updated_node


class MetadataPreservingTransformer(
    MatcherDecoratableTransformer, cst.MetadataDependent
):
    """
    The CSTTransformer equivalent of ContextAwareVisitor. Will preserve metadata passed through a context. You should not chain more than one of these, otherwise metadata will not reflect the state of the tree.
    """

    def __init__(self, context: CodemodContext) -> None:
        MetadataDependent.__init__(self)
        MatcherDecoratableTransformer.__init__(self)
        self.context = context
        if dependencies := self.get_inherited_dependencies():
            if (wrapper := self.context.wrapper) is None:
                raise ValueError(
                    f"Attempting to instantiate {self.__class__.__name__} outside of "
                    + "an active transform. This means that metadata hasn't been "
                    + "calculated and we cannot successfully create this visitor."
                )
            for dep in dependencies:
                if dep not in wrapper._metadata:
                    raise ValueError(
                        f"Attempting to access metadata {dep.__name__} that was not a "
                        + "declared dependency of parent transform! This means it is "
                        + "not possible to compute this value. Please ensure that all "
                        + f"parent transforms of {self.__class__.__name__} declare "
                        + f"{dep.__name__} as a metadata dependency."
                    )
            self.metadata = {dep: wrapper._metadata[dep] for dep in dependencies}


def is_django_settings_file(file_path: Path):
    if "settings.py" not in file_path.name:
        return False
    # the most telling fact is the presence of a manage.py file in the parent directory
    if file_path.parent.parent.is_dir():
        return "manage.py" in (f.name for f in file_path.parent.parent.iterdir())
    return False


def is_setup_py_file(file_path: Path):
    return file_path.name == "setup.py"


def get_call_name(call: cst.Call) -> str:
    """
    Extracts the full name from a function call

    """
    # is it a composite name? e.g. a.b.c
    if matchers.matches(call.func, matchers.Attribute()):
        return call.func.attr.value
    # It's a simple Name
    return call.func.value


def get_function_name_node(call: cst.Call) -> Optional[cst.Name]:
    match call.func:
        case cst.Name():
            return call.func
        case cst.Attribute():
            return call.func.attr
    return None


def is_assigned_to_True(original_node: cst.Assign):
    return (
        isinstance(original_node.value, cst.Name)
        and original_node.value.value == "True"
    )


def is_zero(node: cst.CSTNode) -> bool:
    match node:
        case cst.Integer() | cst.Float():
            try:
                return float(node.value) == 0
            except (ValueError, TypeError):
                return False
        case cst.Call(func=cst.Name("int"), args=[]) | cst.Call(
            func=cst.Name("float"), args=[]
        ):
            # int() or float() == 0
            return True
        case cst.Call(
            func=cst.Name("int"), args=[cst.Arg(value=cst.Name(value="False"))]
        ) | cst.Call(
            func=cst.Name("float"), args=[cst.Arg(value=cst.Name(value="False"))]
        ):
            # int(False) or float(False)
            return True
        case cst.Call(func=cst.Name("int")) | cst.Call(func=cst.Name("float")):
            return is_zero(node.args[0].value)
    return False
