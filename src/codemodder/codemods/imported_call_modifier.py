import abc
from typing import Generic, Mapping, Sequence, Set, TypeVar, Union

import libcst as cst
from libcst import matchers
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand
from libcst.metadata import PositionProvider

from codemodder.change import Change
from codemodder.codemods.utils_mixin import NameResolutionMixin
from codemodder.file_context import FileContext


# It seems to me like we actually want two separate bounds instead of a Union but this is what mypy wants
FunctionMatchType = TypeVar("FunctionMatchType", bound=Union[Mapping, Set])


class ImportedCallModifier(
    Generic[FunctionMatchType],
    VisitorBasedCodemodCommand,
    NameResolutionMixin,
    metaclass=abc.ABCMeta,
):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(
        self,
        codemod_context: CodemodContext,
        file_context: FileContext,
        matching_functions: FunctionMatchType,
        change_description: str,
    ):
        super().__init__(codemod_context)
        self.line_exclude = file_context.line_exclude
        self.line_include = file_context.line_include
        self.matching_functions: FunctionMatchType = matching_functions
        self.change_description = change_description
        self.changes_in_file: list[Change] = []

    def updated_args(self, original_args: Sequence[cst.Arg]):
        return original_args

    @abc.abstractmethod
    def update_attribute(
        self,
        true_name: str,
        original_node: cst.Call,
        updated_node: cst.Call,
        new_args: Sequence[cst.Arg],
    ):
        """Callback to modify tree when the detected call is of the form a.call()"""

    @abc.abstractmethod
    def update_simple_name(
        self,
        true_name: str,
        original_node: cst.Call,
        updated_node: cst.Call,
        new_args: Sequence[cst.Arg],
    ):
        """Callback to modify tree when the detected call is of the form call()"""

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call):
        pos_to_match = self.node_position(original_node)
        line_number = pos_to_match.start.line
        if self.filter_by_path_includes_or_excludes(pos_to_match):
            true_name = self.find_base_name(original_node.func)
            if (
                self._is_direct_call_from_imported_module(original_node)
                and true_name
                and true_name in self.matching_functions
            ):
                self.changes_in_file.append(
                    Change(line_number, self.change_description)
                )

                new_args = self.updated_args(updated_node.args)

                # has a prefix, e.g. a.call() -> a.new_call()
                if matchers.matches(original_node.func, matchers.Attribute()):
                    return self.update_attribute(
                        true_name, original_node, updated_node, new_args
                    )

                # it is a simple name, e.g. call() -> module.new_call()
                return self.update_simple_name(
                    true_name, original_node, updated_node, new_args
                )

        return updated_node

    def filter_by_path_includes_or_excludes(self, pos_to_match):
        """
        Returns False if the node, whose position in the file is pos_to_match, matches any of the lines specified in the path-includes or path-excludes flags.
        """
        # excludes takes precedence if defined
        if self.line_exclude:
            return not any(match_line(pos_to_match, line) for line in self.line_exclude)
        if self.line_include:
            return any(match_line(pos_to_match, line) for line in self.line_include)
        return True

    def node_position(self, node):
        # See https://github.com/Instagram/LibCST/blob/main/libcst/_metadata_dependent.py#L112
        return self.get_metadata(PositionProvider, node)


def match_line(pos, line):
    return pos.start.line == line and pos.end.line == line
