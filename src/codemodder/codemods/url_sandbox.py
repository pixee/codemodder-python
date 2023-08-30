from typing import List, Optional, Union
import libcst as cst
from libcst import CSTNode, matchers
from libcst.codemod import Codemod, CodemodContext
from libcst.metadata import PositionProvider, ScopeProvider
from codemodder.codemods.utils import ReplaceNodes
from codemodder.file_context import FileContext

from libcst.codemod.visitors import AddImportsVisitor, ImportItem
from codemodder.dependency_manager import DependencyManager
from codemodder.codemods.change import Change
from codemodder.codemods.base_codemod import (
    SemgrepCodemod,
    CodemodMetadata,
    ReviewGuidance,
)
from codemodder.codemods.base_visitor import BaseVisitor
from codemodder.codemods.transformations.remove_unused_imports import (
    RemoveUnusedImportsCodemod,
)

replacement_package = "security"
replacement_import = "safe_requests"


class UrlSandbox(SemgrepCodemod, Codemod):
    METADATA = CodemodMetadata(
        DESCRIPTION=(
            "Replaces request.{func} with more secure safe_request library functions."
        ),
        NAME="url-sandbox",
        REVIEW_GUIDANCE=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
    )
    CHANGE_DESCRIPTION = "Switch use of requests for security.safe_requests"
    YAML_FILES = [
        "sandbox_url_creation.yaml",
    ]

    METADATA_DEPENDENCIES = (PositionProvider, ScopeProvider)

    def __init__(self, codemod_context: CodemodContext, file_context: FileContext):
        Codemod.__init__(self, codemod_context)
        SemgrepCodemod.__init__(self, file_context)

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        # we first gather all the nodes we want to change together with their replacements
        find_requests_visitor = FindRequestCallsAndImports(
            self.context, self.file_context, self._results
        )
        tree.visit(find_requests_visitor)
        if find_requests_visitor.nodes_to_change:
            UrlSandbox.CHANGES_IN_FILE.extend(find_requests_visitor.changes_in_file)
            new_tree = tree.visit(ReplaceNodes(find_requests_visitor.nodes_to_change))
            DependencyManager().add(["security==1.0.1"])
            # if it finds any request.get(...), try to remove the imports
            if any(
                (
                    matchers.matches(n, matchers.Call())
                    for n in find_requests_visitor.nodes_to_change
                )
            ):
                new_tree = AddImportsVisitor(
                    self.context,
                    [ImportItem(replacement_package, replacement_import, None, 0)],
                ).transform_module(new_tree)
                new_tree = RemoveUnusedImportsCodemod(self.context).transform_module(
                    new_tree
                )
            return new_tree
        return tree


class FindRequestCallsAndImports(BaseVisitor):
    METADATA_DEPENDENCIES = (*BaseVisitor.METADATA_DEPENDENCIES, ScopeProvider)

    def __init__(
        self, codemod_context: CodemodContext, file_context: FileContext, results
    ):
        super().__init__(
            codemod_context,
            results,
            file_context.line_exclude,
            file_context.line_include,
        )
        self.nodes_to_change: dict[
            cst.CSTNode, Union[cst.CSTNode, cst.FlattenSentinel, cst.RemovalSentinel]
        ] = {}
        self.changes_in_file: List[Change] = []

    def leave_Call(self, original_node: cst.Call):
        pos_to_match = self.node_position(original_node)
        if self.filter_by_result(
            pos_to_match
        ) and self.filter_by_path_includes_or_excludes(pos_to_match):
            line_number = pos_to_match.start.line
            # case get(...)
            if matchers.matches(original_node, matchers.Call(func=matchers.Name())):
                # find if get(...) comes from an from requests import get
                maybe_node = self.find_single_assignment(original_node)
                if maybe_node and matchers.matches(maybe_node, matchers.ImportFrom()):
                    self.nodes_to_change.update(
                        {
                            maybe_node: cst.ImportFrom(
                                module=cst.parse_expression(
                                    replacement_package + "." + replacement_import
                                ),
                                names=maybe_node.names,
                            )
                        }
                    )
                    self.changes_in_file.append(
                        Change(
                            str(line_number), UrlSandbox.CHANGE_DESCRIPTION
                        ).to_json()
                    )

            # case req.get(...)
            else:
                self.nodes_to_change.update(
                    {
                        original_node: cst.Call(
                            func=cst.parse_expression(replacement_import + ".get"),
                            args=original_node.args,
                        )
                    }
                )
                self.changes_in_file.append(
                    Change(str(line_number), UrlSandbox.CHANGE_DESCRIPTION).to_json()
                )

    def _find_assignments(self, node: CSTNode):
        """
        Given a MetadataWrapper and a CSTNode representing an access, find all the possible assignments that it refers.
        """
        scope = self.get_metadata(ScopeProvider, node)
        # pylint: disable=protected-access
        return next(iter(scope.accesses[node]))._Access__assignments

    def find_single_assignment(self, node: CSTNode) -> Optional[CSTNode]:
        """
        Given a MetadataWrapper and a CSTNode representing an access, find if there is a single assignment that it refers to.
        """
        assignments = self._find_assignments(node)
        if len(assignments) == 1:
            return next(iter(assignments)).node
        return None
