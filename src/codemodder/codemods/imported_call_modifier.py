import abc
from typing import Generic, Mapping, Sequence, Set, TypeVar, Union

import libcst as cst
from libcst import matchers
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand
from libcst.metadata import ParentNodeProvider, PositionProvider

from codemodder.codemods.base_visitor import UtilsMixin
from codemodder.codemods.utils_mixin import NameResolutionMixin
from codemodder.codetf import Change
from codemodder.file_context import FileContext
from codemodder.result import Result

# It seems to me like we actually want two separate bounds instead of a Union but this is what mypy wants
FunctionMatchType = TypeVar("FunctionMatchType", bound=Union[Mapping, Set])


class ImportedCallModifier(
    Generic[FunctionMatchType],
    VisitorBasedCodemodCommand,
    NameResolutionMixin,
    UtilsMixin,
    metaclass=abc.ABCMeta,
):
    METADATA_DEPENDENCIES = (ParentNodeProvider, PositionProvider)

    def __init__(
        self,
        codemod_context: CodemodContext,
        file_context: FileContext,
        matching_functions: FunctionMatchType,
        change_description: str,
        results: list[Result] | None = None,
    ):
        VisitorBasedCodemodCommand.__init__(self, codemod_context)
        self.line_exclude = file_context.line_exclude
        self.line_include = file_context.line_include
        self.matching_functions: FunctionMatchType = matching_functions
        self.change_description = change_description
        self.changes_in_file: list[Change] = []
        self.results = results
        self.file_context = file_context

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
        if self.node_is_selected(
            original_node
        ) and self.filter_by_path_includes_or_excludes(pos_to_match):
            true_name = self.find_base_name(original_node.func)
            if (
                self.is_direct_call_from_imported_module(original_node)
                and true_name
                and true_name in self.matching_functions
            ):
                self.changes_in_file.append(
                    Change(
                        lineNumber=line_number,
                        description=self.change_description,
                        findings=self.file_context.get_findings_for_location(
                            line_number
                        ),
                    )
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
