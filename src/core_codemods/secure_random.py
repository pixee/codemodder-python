from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import SemgrepCodemod


class SecureRandom(SemgrepCodemod):
    NAME = "secure-random"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW
    SUMMARY = "Secure Source of Randomness"
    DESCRIPTION = "Replaces random.{func} with more secure secrets library functions."
    REFERENCES = [
        {
            "url": "https://owasp.org/www-community/vulnerabilities/Insecure_Randomness",
            "description": "",
        },
        {"url": "https://docs.python.org/3/library/random.html", "description": ""},
    ]

    @classmethod
    def rule(cls):
        return """
        rules:
          - patterns:
            - pattern: random.$F(...)
            - pattern-not: random.SystemRandom()
            - pattern-inside: |
                import random
                ...
        """

    def on_result_found(self, original_node, updated_node):
        self.remove_unused_import(original_node)
        self.add_needed_import("secrets")
        return self.update_call_target(updated_node, "secrets.SystemRandom()")
