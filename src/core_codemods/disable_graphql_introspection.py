import libcst as cst
from libcst.codemod import CodemodContext, ContextAwareVisitor

from codemodder.codemods.base_codemod import Metadata, ReviewGuidance
from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.codemods.utils import ReplacementNodeType, ReplaceNodes
from codemodder.codemods.utils_mixin import NameAndAncestorResolutionMixin
from codemodder.codetf import Reference
from core_codemods.api.core_codemod import CoreCodemod


class DisableGraphQLIntrospectionTransform(
    LibcstResultTransformer, NameAndAncestorResolutionMixin
):

    change_description = "Added rule to disable introspection"

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        visitor = FindGraphQLViewsWithIntrospection(self.context)
        tree.visit(visitor)
        all_changes: dict[cst.CSTNode, ReplacementNodeType] = {}
        for call, changes in visitor.calls_to_change.items():
            if self.node_is_selected(call.func) or self.node_is_selected(call):
                all_changes |= changes
                self.report_change(call)
        if all_changes:
            self.add_needed_import(
                "graphql.validation", "NoSchemaIntrospectionCustomRule"
            )
            return tree.visit(ReplaceNodes(all_changes))
        return super().transform_module_impl(tree)


class FindGraphQLViewsWithIntrospection(
    ContextAwareVisitor, NameAndAncestorResolutionMixin
):

    supported_functions = {
        "graphql_server.flask.GraphQLView",
        "graphql_server.flask.GraphQLView.as_view",
        "graphql_server.sanic.GraphQLView",
        "graphql_server.aiohttp.GraphQLView",
        "graphql_server.webob.GraphQLView",
    }

    introspection_rules_objects = {
        "graphql.validation.NoSchemaIntrospectionCustomRule",
        "graphql.NoSchemaIntrospectionCustomRule",
        "graphene.validation.DisableIntrospection",
    }

    def __init__(self, context: CodemodContext) -> None:
        self.calls_to_change: dict[cst.Call, dict[cst.CSTNode, ReplacementNodeType]] = (
            {}
        )
        super().__init__(context)

    def leave_Call(self, original_node: cst.Call):
        # accumulates the changes associated with the detected call
        nodes_to_change = {}
        if self.find_base_name(original_node) in self.supported_functions:
            resolved_args = self.resolve_keyword_args(original_node)
            if "validation_rules" in resolved_args.keys():
                # is it a list literal that I can append?
                resolved = resolved_args["validation_rules"]
                match resolved:
                    case cst.List():
                        # does it have any introspection rule
                        if not any(
                            filter(
                                lambda e: self._is_introspection_rule_or_starred(e),
                                self.resolve_list_literal(resolved),
                            )
                        ):
                            nodes_to_change[resolved] = resolved.with_changes(
                                elements=[
                                    *resolved.elements,
                                    cst.Element(
                                        value=cst.Name(
                                            "NoSchemaIntrospectionCustomRule"
                                        )
                                    ),
                                ]
                            )

            else:
                nodes_to_change[original_node] = original_node.with_changes(
                    args=[
                        *original_node.args,
                        cst.Arg(
                            value=cst.parse_expression(
                                "[NoSchemaIntrospectionCustomRule,]"
                            ),
                            keyword=cst.Name("validation_rules"),
                        ),
                    ]
                )
        if nodes_to_change:
            self.calls_to_change[original_node] = nodes_to_change

    def _is_introspection_rule_or_starred(
        self, node: cst.BaseExpression | cst.StarredElement
    ) -> bool:
        # Does it have a starred element?
        if isinstance(node, cst.StarredElement):
            return True
        if isinstance(node, cst.Name):
            return self.find_base_name(node) in self.introspection_rules_objects
        return False


DisableGraphQLIntrospection = CoreCodemod(
    metadata=Metadata(
        name="disable-graphql-introspection",
        summary="Disable GraphQL Introspection to Prevent Sensitive Data Leakage",
        review_guidance=ReviewGuidance.MERGE_AFTER_REVIEW,
        references=[
            Reference(
                url="https://owasp.org/Top10/A05_2021-Security_Misconfiguration/",
            ),
            Reference(
                url="https://owasp.org/www-project-top-ten/2017/A3_2017-Sensitive_Data_Exposure",
            ),
            Reference(
                url="https://owasp.org/www-project-web-security-testing-guide/v42/4-Web_Application_Security_Testing/12-API_Testing/01-Testing_GraphQL#introspection-queries",
            ),
        ],
    ),
    transformer=LibcstTransformerPipeline(DisableGraphQLIntrospectionTransform),
    detector=None,
)
