from typing import List, Optional, Union

import libcst as cst
from libcst import CSTNode, matchers
from libcst.codemod import Codemod, CodemodContext
from libcst.metadata import PositionProvider, ScopeProvider

from libcst.codemod.visitors import AddImportsVisitor, ImportItem
from codemodder.change import Change
from codemodder.codemods.base_codemod import (
    SemgrepCodemod,
    CodemodMetadata,
    ReviewGuidance,
)
from codemodder.codemods.base_visitor import BaseVisitor
from codemodder.codemods.transformations.remove_unused_imports import (
    RemoveUnusedImportsCodemod,
)
from codemodder.codemods.utils import ReplaceNodes
from codemodder.dependency import Security
from codemodder.file_context import FileContext


replacement_import = "safe_requests"


class UrlSandbox(SemgrepCodemod, Codemod):
    METADATA = CodemodMetadata(
        DESCRIPTION=(
            "Replaces request.{func} with more secure safe_request library functions."
        ),
        NAME="url-sandbox",
        REVIEW_GUIDANCE=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
        REFERENCES=[
            {
                "url": "https://github.com/pixee/python-security/blob/main/src/security/safe_requests/api.py",
                "description": "",
            },
            {"url": "https://portswigger.net/web-security/ssrf", "description": ""},
            {
                "url": "https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html",
                "description": "",
            },
            {
                "url": "https://www.rapid7.com/blog/post/2021/11/23/owasp-top-10-deep-dive-defending-against-server-side-request-forgery/",
                "description": "",
            },
            {
                "url": "https://blog.assetnote.io/2021/01/13/blind-ssrf-chains/",
                "description": "",
            },
        ],
    )
    SUMMARY = "Sandbox URL Creation"
    CHANGE_DESCRIPTION = "Switch use of requests for security.safe_requests"
    YAML_FILES = [
        "sandbox_url_creation.yaml",
    ]

    METADATA_DEPENDENCIES = (PositionProvider, ScopeProvider)

    adds_dependency = True

    def __init__(self, codemod_context: CodemodContext, *args):
        Codemod.__init__(self, codemod_context)
        SemgrepCodemod.__init__(self, *args)

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        # we first gather all the nodes we want to change together with their replacements
        find_requests_visitor = FindRequestCallsAndImports(
            self.context,
            self.file_context,
            self.file_context.findings,
        )
        tree.visit(find_requests_visitor)
        if find_requests_visitor.nodes_to_change:
            self.file_context.codemod_changes.extend(
                find_requests_visitor.changes_in_file
            )
            new_tree = tree.visit(ReplaceNodes(find_requests_visitor.nodes_to_change))
            self.add_dependency(Security)
            # if it finds any request.get(...), try to remove the imports
            if any(
                (
                    matchers.matches(n, matchers.Call())
                    for n in find_requests_visitor.nodes_to_change
                )
            ):
                new_tree = AddImportsVisitor(
                    self.context,
                    [ImportItem(Security.name, replacement_import, None, 0)],
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
        super().__init__(codemod_context, results)
        self.line_exclude = file_context.line_exclude
        self.line_include = file_context.line_include
        self.nodes_to_change: dict[
            cst.CSTNode, Union[cst.CSTNode, cst.FlattenSentinel, cst.RemovalSentinel]
        ] = {}
        self.changes_in_file: List[Change] = []

    def leave_Call(self, original_node: cst.Call):
        pos_to_match = self.node_position(original_node)
        if not (
            self.filter_by_result(pos_to_match)
            and self.filter_by_path_includes_or_excludes(pos_to_match)
        ):
            return

        line_number = pos_to_match.start.line
        match original_node.args[0].value:
            case cst.SimpleString():
                return

        match original_node:
            # case get(...)
            case cst.Call(func=cst.Name()):
                # find if get(...) comes from an from requests import get
                match self.find_single_assignment(original_node):
                    case cst.ImportFrom() as node:
                        self.nodes_to_change.update(
                            {
                                node: cst.ImportFrom(
                                    module=cst.Attribute(
                                        value=cst.Name(Security.name),
                                        attr=cst.Name(replacement_import),
                                    ),
                                    names=node.names,
                                )
                            }
                        )
                        self.changes_in_file.append(
                            Change(line_number, UrlSandbox.CHANGE_DESCRIPTION)
                        )

            # case req.get(...)
            case _:
                self.nodes_to_change.update(
                    {
                        original_node: cst.Call(
                            func=cst.parse_expression(replacement_import + ".get"),
                            args=original_node.args,
                        )
                    }
                )
                self.changes_in_file.append(
                    Change(line_number, UrlSandbox.CHANGE_DESCRIPTION)
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
