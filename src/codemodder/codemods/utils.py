from pathlib import Path
from typing import Optional, Any

from libcst import matchers
import libcst as cst


class SequenceExtension:
    def __init__(self, sequence: list[cst.CSTNode]) -> None:
        self.sequence = sequence


class Append(SequenceExtension):
    pass


class Prepend(SequenceExtension):
    pass


class ReplaceNodes(cst.CSTTransformer):
    """
    Replace nodes with their corresponding values in a given dict. The replacements dictionary should either contain a mapping from a node to another node, RemovalSentinel, or FlattenSentinel to be replaced, or a dict mapping each attribute, by name, to a new value. Additionally if the attribute is a sequence, you may pass Append(l)/Prepend(l), where l is a list of nodes, to append or prepend, respectively.
    """

    def __init__(
        self,
        replacements: dict[
            cst.CSTNode,
            dict[
                str,
                cst.CSTNode
                | cst.FlattenSentinel
                | cst.RemovalSentinel
                | dict[str, Any],
            ],
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


def is_django_settings_file(file_path: Path):
    if "settings.py" not in file_path.name:
        return False
    # the most telling fact is the presence of a manage.py file in the parent directory
    if file_path.parent.parent.is_dir():
        return "manage.py" in (f.name for f in file_path.parent.parent.iterdir())
    return False


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
