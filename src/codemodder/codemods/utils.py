from pathlib import Path
from typing import Union

from libcst import matchers
import libcst as cst


class ReplaceNodes(cst.CSTTransformer):
    """
    Replace nodes with their corresponding values in a given dict.
    """

    def __init__(
        self,
        replacements: dict[
            cst.CSTNode,
            Union[cst.CSTNode, cst.FlattenSentinel[cst.CSTNode], cst.RemovalSentinel],
        ],
    ):
        self.replacements = replacements

    def on_leave(self, original_node, updated_node):
        if original_node in self.replacements.keys():
            return self.replacements[original_node]
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
