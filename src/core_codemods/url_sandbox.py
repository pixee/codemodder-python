from typing import List, Optional, Union

import libcst as cst
from libcst import CSTNode, matchers
from libcst.codemod import CodemodContext, ContextAwareVisitor
from libcst.codemod.visitors import AddImportsVisitor, ImportItem
from libcst.metadata import PositionProvider, ScopeProvider

from codemodder.codemods.base_visitor import UtilsMixin
from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.codemods.semgrep import SemgrepRuleDetector
from codemodder.codemods.transformations.remove_unused_imports import (
    RemoveUnusedImportsCodemod,
)
from codemodder.codemods.utils import ReplaceNodes
from codemodder.codetf import Change
from codemodder.dependency import Security
from codemodder.file_context import FileContext
from core_codemods.api import CoreCodemod, Metadata, Reference, ReviewGuidance

replacement_import = "safe_requests"


class UrlSandboxTransformer(LibcstResultTransformer):
    change_description = "Switch use of requests for security.safe_requests"
    METADATA_DEPENDENCIES = (PositionProvider, ScopeProvider)
    adds_dependency = True

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        # we first gather all the nodes we want to change together with their replacements
        find_requests_visitor = FindRequestCallsAndImports(
            self.context,
            self.file_context,
            self.file_context.results,
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


class FindRequestCallsAndImports(ContextAwareVisitor, UtilsMixin):
    METADATA_DEPENDENCIES = (ScopeProvider,)

    def __init__(
        self, codemod_context: CodemodContext, file_context: FileContext, results
    ):
        self.nodes_to_change: dict[
            cst.CSTNode, Union[cst.CSTNode, cst.FlattenSentinel, cst.RemovalSentinel]
        ] = {}
        self.changes_in_file: List[Change] = []
        ContextAwareVisitor.__init__(self, codemod_context)
        UtilsMixin.__init__(
            self,
            results=results,
            line_include=file_context.line_include,
            line_exclude=file_context.line_exclude,
        )

    def leave_Call(self, original_node: cst.Call):
        if not self.node_is_selected(original_node):
            return

        line_number = self.node_position(original_node).start.line
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
                            Change(
                                lineNumber=line_number,
                                description=UrlSandboxTransformer.change_description,
                            )
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
                    Change(
                        lineNumber=line_number,
                        description=UrlSandboxTransformer.change_description,
                    )
                )

    def _find_assignments(self, node: CSTNode):
        """
        Given a MetadataWrapper and a CSTNode representing an access, find all the possible assignments that it refers.
        """
        scope = self.get_metadata(ScopeProvider, node)
        return next(iter(scope.accesses[node]))._Access__assignments

    def find_single_assignment(self, node: CSTNode) -> Optional[CSTNode]:
        """
        Given a MetadataWrapper and a CSTNode representing an access, find if there is a single assignment that it refers to.
        """
        assignments = self._find_assignments(node)
        if len(assignments) == 1:
            return next(iter(assignments)).node
        return None


UrlSandbox = CoreCodemod(
    metadata=Metadata(
        name="url-sandbox",
        summary="Sandbox URL Creation",
        review_guidance=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
        references=[
            Reference(
                url="https://github.com/pixee/python-security/blob/main/src/security/safe_requests/api.py"
            ),
            Reference(url="https://portswigger.net/web-security/ssrf"),
            Reference(
                url="https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html"
            ),
            Reference(
                url="https://www.rapid7.com/blog/post/2021/11/23/owasp-top-10-deep-dive-defending-against-server-side-request-forgery/"
            ),
            Reference(url="https://blog.assetnote.io/2021/01/13/blind-ssrf-chains/"),
        ],
    ),
    detector=SemgrepRuleDetector(
        """
    rules:
      - id: url-sandbox
        message: Unbounded URL creation
        severity: WARNING
        languages:
          - python
        pattern-either:
          - patterns:
            - pattern: requests.get(...)
            - pattern-not: requests.get("...")
            - pattern-inside: |
                import requests
                ...
            """
    ),
    transformer=LibcstTransformerPipeline(UrlSandboxTransformer),
)
