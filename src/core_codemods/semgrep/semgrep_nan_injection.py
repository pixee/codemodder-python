from textwrap import dedent

import libcst as cst
from libcst.codemod import ContextAwareVisitor

from codemodder.codemods.base_codemod import (
    Metadata,
    ReviewGuidance,
    ToolMetadata,
    ToolRule,
)
from codemodder.codemods.base_visitor import UtilsMixin
from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.codemods.semgrep import SemgrepSarifFileDetector
from codemodder.codetf import Reference
from core_codemods.semgrep.api import SemgrepCodemod, semgrep_url_from_id


class NanInjectionTransformer(LibcstResultTransformer):
    change_description = "Add validation to untrusted numerical input to disallow `nan`"

    def leave_SimpleStatementLine(
        self,
        original_node: cst.SimpleStatementLine,
        updated_node: cst.SimpleStatementLine,
    ):

        visitor = MatchNodesInLineVisitor(
            self.context, file_context=self.file_context, results=self.results
        )
        original_node.body[0].visit(visitor)
        if visitor.matched_nodes:
            # For now only handle one matched Call node in a line
            return self.replace_with_if_else(
                visitor.matched_nodes[0], original_node, updated_node
            )
        return original_node

    def replace_with_if_else(
        self,
        node: cst.Call,
        original_node: cst.SimpleStatementLine,
        updated_node: cst.SimpleStatementLine,
    ):
        if not (target_node := self._get_target_in_call(node)):
            return original_node

        code = dedent(
            f"""\
        if {self.code(target_node).strip()}.lower() == "nan":
            raise ValueError
        else:
            {self.code(original_node).strip()}
        """
        )
        self._report_new_lines(original_node)
        new_statement = cst.parse_statement(code)
        return new_statement.with_changes(leading_lines=updated_node.leading_lines)

    def _get_target_in_call(self, node: cst.Call) -> cst.CSTNode:
        match (wrapped_node := node.args[0].value):
            case cst.Name():
                # float(var)
                return wrapped_node

            case cst.Call(
                func=cst.Name("float") | cst.Name("bool") | cst.Name("complex")
            ):
                # bool(float(var)), complex(float(var)), bool(float(var)), etc
                return self._get_target_in_call(wrapped_node)
            case cst.Call() | cst.BinaryOperation():
                return wrapped_node

    def _report_new_lines(self, original_node: cst.SimpleStatementLine):
        self.report_change(original_node)
        line_number = self.lineno_for_node(original_node)
        findings = self.file_context.get_findings_for_location(line_number)
        for lineno in range(line_number + 1, line_number + 4):
            self.report_change_for_line(lineno, findings=findings)


class MatchNodesInLineVisitor(ContextAwareVisitor, UtilsMixin):
    """Visit Call nodes and match if node location matches results."""

    def __init__(
        self,
        context,
        file_context,
        results,
    ) -> None:
        self.file_context = file_context
        ContextAwareVisitor.__init__(self, context)
        UtilsMixin.__init__(
            self,
            results=results,
            line_include=file_context.line_include,
            line_exclude=file_context.line_exclude,
        )

        self.matched_nodes: list[cst.Call] = []

    def visit_Call(self, node: cst.Call) -> None:
        if self.node_is_selected(node):
            self.matched_nodes.append(node)


SemgrepNanInjection = SemgrepCodemod(
    metadata=Metadata(
        name="nan-injection",
        summary=NanInjectionTransformer.change_description.title(),
        description=NanInjectionTransformer.change_description.title(),
        review_guidance=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
        tool=ToolMetadata(
            name="Semgrep",
            rules=[
                ToolRule(
                    id=(
                        rule_id := "python.django.security.nan-injection.nan-injection"
                    ),
                    name="nan-injection",
                    url=semgrep_url_from_id(rule_id),
                )
            ],
        ),
        references=[
            Reference(url="https://cwe.mitre.org/data/definitions/704"),
        ],
    ),
    transformer=LibcstTransformerPipeline(NanInjectionTransformer),
    detector=SemgrepSarifFileDetector(),
    requested_rules=[rule_id],
)
