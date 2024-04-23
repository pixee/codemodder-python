import libcst as cst
from libcst.codemod import CodemodContext, ContextAwareVisitor
from libcst.metadata import (
    ImportAssignment,
    ParentNodeProvider,
    PositionProvider,
    ScopeProvider,
)

from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.codemods.utils import ReplaceNodes
from codemodder.codemods.utils_mixin import NameAndAncestorResolutionMixin
from codemodder.dependency import Security
from core_codemods.api import CoreCodemod, Metadata, Reference, ReviewGuidance

replacement_import = "safe_requests"


class UrlSandboxTransformer(LibcstResultTransformer):
    change_description = "Switch use of requests for security.safe_requests"
    adds_dependency = True

    METADATA_DEPENDENCIES = (
        ScopeProvider,
        PositionProvider,
        ParentNodeProvider,
    )

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        visitor = UrlSandboxVisitor(self.context)
        tree.visit(visitor)
        nodes_to_change = {}
        for call, (original, replacement) in visitor.calls_to_change.items():
            if self.node_is_selected(call):
                if not isinstance(original, cst.ImportFrom | cst.Import):
                    self.add_needed_import("security", replacement_import)
                    self.remove_unused_import(call)
                self.report_change(call, self.change_description)
                nodes_to_change[original] = replacement
                self.add_dependency(Security)
        if nodes_to_change:
            result = tree.visit(ReplaceNodes(nodes_to_change))
            print(tree.code)
            print(result.code)
            return result

        return tree


class UrlSandboxVisitor(ContextAwareVisitor, NameAndAncestorResolutionMixin):

    def __init__(self, context: CodemodContext) -> None:
        self.calls_to_change: dict[cst.Call, tuple[cst.CSTNode, cst.CSTNode]] = {}
        super().__init__(context)

    def leave_Call(self, original_node: cst.Call):
        # is first arg a hardcoded string?
        match original_node.args:
            case [cst.Arg(value=first_arg), *_]:
                resolved_arg = self.resolve_expression(first_arg)
                if isinstance(resolved_arg, cst.SimpleString):
                    return

        resolved = self.resolve_expression(original_node)
        true_name = self.find_base_name(resolved)
        if true_name in ("requests.get",):
            # is it aliased? (i.e. get(...) or requests.get(...))
            match resolved:
                case cst.Call(func=cst.Name()):
                    origin = self.find_single_assignment(resolved)
                    # sanity check mostly, ImportFrom is the only possibility here
                    match origin:
                        case ImportAssignment(node=cst.ImportFrom() as node):

                            self.calls_to_change[original_node] = (
                                node,
                                cst.ImportFrom(
                                    module=cst.Attribute(
                                        value=cst.Name(Security.name),
                                        attr=cst.Name(replacement_import),
                                    ),
                                    names=node.names,
                                ),
                            )
                case _:
                    maybe_imported = self.get_imported_prefix(original_node)
                    if maybe_imported:
                        self.calls_to_change[original_node] = (
                            original_node,
                            cst.Call(
                                func=cst.parse_expression(replacement_import + ".get"),
                                args=original_node.args,
                            ),
                        )


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
    detector=None,
    transformer=LibcstTransformerPipeline(UrlSandboxTransformer),
)
