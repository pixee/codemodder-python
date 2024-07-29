import libcst as cst

from codemodder.codemods.base_codemod import (
    Metadata,
    ReviewGuidance,
    ToolMetadata,
    ToolRule,
)
from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.codemods.semgrep import SemgrepSarifFileDetector
from codemodder.codemods.utils_mixin import NameResolutionMixin
from core_codemods.semgrep.api import SemgrepCodemod, semgrep_url_from_id


class RemoveCsrfExemptTransformer(LibcstResultTransformer, NameResolutionMixin):
    change_description = "Remove `@csrf_exempt` decorator from Django view"

    def leave_Decorator(
        self, original_node: cst.Decorator, updated_node: cst.Decorator
    ):
        if not self.filter_by_path_includes_or_excludes(
            self.node_position(original_node)
        ):
            return updated_node

        if (
            self.find_base_name(original_node.decorator)
            == "django.views.decorators.csrf.csrf_exempt"
        ):
            self.report_change(original_node)
            return cst.RemovalSentinel.REMOVE
        return original_node


SemgrepNoCsrfExempt = SemgrepCodemod(
    metadata=Metadata(
        name="no-csrf-exempt",
        summary=RemoveCsrfExemptTransformer.change_description.title(),
        description=RemoveCsrfExemptTransformer.change_description.title(),
        review_guidance=ReviewGuidance.MERGE_AFTER_REVIEW,
        tool=ToolMetadata(
            name="Semgrep",
            rules=[
                ToolRule(
                    id=(
                        rule_id := "python.django.security.audit.csrf-exempt.no-csrf-exempt"
                    ),
                    name="no-csrf-exempt",
                    url=semgrep_url_from_id(rule_id),
                )
            ],
        ),
        references=[],
    ),
    transformer=LibcstTransformerPipeline(RemoveCsrfExemptTransformer),
    detector=SemgrepSarifFileDetector(),
    requested_rules=[rule_id],
)
