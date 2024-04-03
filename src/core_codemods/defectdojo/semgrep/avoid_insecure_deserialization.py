import libcst as cst

from codemodder.codemods.api import Metadata, ReviewGuidance, ToolMetadata
from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.codemods.utils_mixin import NameResolutionMixin
from core_codemods.defectdojo.api import DefectDojoCodemod, DefectDojoDetector
from core_codemods.harden_pickle_load import HardenPickleLoad
from core_codemods.harden_pyyaml import CodemodProtocol, HardenPyyamlCallMixin


class AvoidInsecureDeserializationTransformer(
    LibcstResultTransformer,
    NameResolutionMixin,
    HardenPyyamlCallMixin,
    CodemodProtocol,
):
    def leave_Call(
        self, original_node: cst.Call, updated_node: cst.Call
    ) -> cst.Call | None:
        if (
            self.node_is_selected(original_node)
            and self.find_base_name(original_node) == "yaml.load"
        ):
            self.report_change(
                original_node, description="Use SafeLoader in pyyaml.load calls"
            )
            return self.update_call(original_node, updated_node)

        return updated_node


AvoidInsecureDeserialization = DefectDojoCodemod(
    metadata=Metadata(
        name="avoid-insecure-deserialization",
        summary="Harden potentially insecure deserialization operations",
        review_guidance=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
        tool=ToolMetadata(
            name="DefectDojo",
            rule_id="python.django.security.audit.avoid-insecure-deserialization.avoid-insecure-deserialization",
            rule_name="avoid-insecure-deserialization",
            rule_url="https://semgrep.dev/playground/r/python.django.security.audit.avoid-insecure-deserialization.avoid-insecure-deserialization",
        ),
        references=[],
    ),
    transformer=LibcstTransformerPipeline(
        AvoidInsecureDeserializationTransformer, HardenPickleLoad
    ),
    detector=DefectDojoDetector(),
)
