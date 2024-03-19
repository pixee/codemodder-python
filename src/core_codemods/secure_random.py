from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.codemods.semgrep import SemgrepRuleDetector
from codemodder.codemods.utils_mixin import NameResolutionMixin
from core_codemods.api import CoreCodemod, Metadata, Reference, ReviewGuidance


class SecureRandomTransformer(LibcstResultTransformer, NameResolutionMixin):
    change_description = (
        "Replace random.{func} with more secure secrets library functions."
    )

    def on_result_found(self, original_node, updated_node):
        self.remove_unused_import(original_node)
        self.add_needed_import("secrets")

        if self.find_base_name(original_node.func) == "random.choice":
            return self.update_call_target(updated_node, "secrets")
        return self.update_call_target(updated_node, "secrets.SystemRandom()")


SecureRandom = CoreCodemod(
    metadata=Metadata(
        name="secure-random",
        review_guidance=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
        summary="Secure Source of Randomness",
        references=[
            Reference(
                url="https://owasp.org/www-community/vulnerabilities/Insecure_Randomness",
            ),
            Reference(
                url="https://docs.python.org/3/library/random.html",
            ),
        ],
    ),
    detector=SemgrepRuleDetector(
        """
            - patterns:
              - pattern: random.$F(...)
              - pattern-not: random.SystemRandom()
              - pattern-inside: |
                  import random
                  ...
        """
    ),
    transformer=LibcstTransformerPipeline(SecureRandomTransformer),
)
