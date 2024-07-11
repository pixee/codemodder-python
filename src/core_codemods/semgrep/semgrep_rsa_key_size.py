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
    NewArg,
)
from codemodder.codemods.semgrep import SemgrepSarifFileDetector
from codemodder.result import fuzzy_column_match, same_line
from core_codemods.semgrep.api import SemgrepCodemod, semgrep_url_from_id

RSA_KEYSIZE = "2048"


class RsaKeySizeTransformer(LibcstResultTransformer):
    change_description = "Change the RSA key size to 2048"

    def on_result_found(self, original_node, updated_node):
        if len(original_node.args) < 2:
            return original_node

        if original_node.args[1].keyword is None:
            new_args = [original_node.args[0], self.make_new_arg(RSA_KEYSIZE)]
        else:
            new_args = self.replace_args(
                original_node,
                [NewArg(name="key_size", value=RSA_KEYSIZE, add_if_missing=False)],
            )
        return self.update_arg_target(updated_node, new_args)

    def filter_by_result(self, node) -> bool:
        """
        Special case result-matching for this rule because the SAST
        results returned have a start/end column for the key_size keyword
        within the call, not for the entire call.
        """
        match node:
            case cst.Call():
                pos_to_match = self.node_position(node)
                return any(
                    self.match_location(pos_to_match, result)
                    for result in self.results or []
                )
        return False

    def match_location(self, pos, result):
        return any(
            same_line(pos, location) and fuzzy_column_match(pos, location)
            for location in result.locations
        )


SemgrepRsaKeySize = SemgrepCodemod(
    metadata=Metadata(
        name="rsa-key-size",
        summary=RsaKeySizeTransformer.change_description.title(),
        description=RsaKeySizeTransformer.change_description.title(),
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        tool=ToolMetadata(
            name="Semgrep",
            rules=[
                ToolRule(
                    id=(
                        rule_id := "python.cryptography.security.insufficient-rsa-key-size.insufficient-rsa-key-size"
                    ),
                    name="insufficient-rsa-key-size",
                    url=semgrep_url_from_id(rule_id),
                )
            ],
        ),
        references=[],
    ),
    transformer=LibcstTransformerPipeline(RsaKeySizeTransformer),
    detector=SemgrepSarifFileDetector(),
    requested_rules=[rule_id],
)
