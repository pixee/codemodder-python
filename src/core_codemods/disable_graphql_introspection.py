from itertools import chain

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

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        visitor = FindGraphQLViewsWithIntrospection(self.context)
        tree.visit(visitor)
        all_changes: dict[cst.CSTNode, ReplacementNodeType] = {}
        for call, changes in visitor.calls_to_change.items():
            if self.node_is_selected(call):
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
                        print(list(self.resolve_list_literal(resolved)))
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
        print(node)
        if isinstance(node, cst.Name):
            return self.find_base_name(node.value) in self.introspection_rules_objects
        return False

    def _resolve_starred_element(self, element: cst.StarredElement):
        resolved = self.resolve_expression(element.value)
        match resolved:
            case cst.List():
                return self.resolve_list_literal(resolved)
        return [element]

    def _resolve_list_element(self, element: cst.BaseElement):
        match element:
            case cst.Element():
                return [self.resolve_expression(element.value)]
            case cst.StarredElement():
                return self._resolve_starred_element(element)
        return []

    def resolve_list_literal(self, list_literal: cst.List):
        """
        Returns an iterable of all the elements of that list resolved. It will recurse into starred elements whenever possible.
        """
        return chain.from_iterable(
            map(self._resolve_list_element, list_literal.elements)
        )

    def _resolve_starred_dict_element(self, element: cst.StarredDictElement):
        resolved = self.resolve_expression(element.value)
        match resolved:
            case cst.Dict():
                return self.resolve_dict(resolved)
        return dict()

    def _resolve_dict_element(self, element: cst.BaseDictElement):
        match element:
            case cst.StarredDictElement():
                return self._resolve_starred_dict_element(element)
            case _:
                resolved_key = self.resolve_expression(element.key)
                resolved_key_value = resolved_key
                match resolved_key:
                    case cst.SimpleString():
                        resolved_key_value = resolved_key.raw_value
                resolved_value = self.resolve_expression(element.value)
                return {resolved_key_value: resolved_value}

    def resolve_dict(self, dictionary: cst.Dict):
        compilation = dict()
        for e in dictionary.elements:
            compilation.update(self._resolve_dict_element(e))
        return compilation

    def resolve_keyword_args(self, call: cst.Call):
        """
        Returns a dict with all the keyword arguments resolved. It will recurse into starred elements whenever possible.
        """
        keyword_to_expr_dict: dict = dict()
        for arg in call.args:
            if arg.star == "**":
                resolved = self.resolve_expression(arg.value)
                match resolved:
                    case cst.Dict():
                        keyword_to_expr_dict |= self.resolve_dict(resolved)
            if arg.keyword:
                keyword_to_expr_dict |= {
                    arg.keyword.value: self.resolve_expression(arg.value)
                }
        return keyword_to_expr_dict


DisableGraphQLIntrospection = CoreCodemod(
    metadata=Metadata(
        name="disable-graphql-introspection",
        summary="",
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
