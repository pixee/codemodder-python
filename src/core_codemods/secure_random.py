from core_codemods.api import (
    SimpleCodemod,
    Metadata,
    Reference,
    ReviewGuidance,
)


class SecureRandom(SimpleCodemod):
    metadata = Metadata(
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
    )

    detector_pattern = """
        - patterns:
          - pattern: random.$F(...)
          - pattern-not: random.SystemRandom()
          - pattern-inside: |
              import random
              ...
    """

    change_description = (
        "Replace random.{func} with more secure secrets library functions."
    )

    def on_result_found(self, original_node, updated_node):
        self.remove_unused_import(original_node)
        self.add_needed_import("secrets")
        return self.update_call_target(updated_node, "secrets.SystemRandom()")
