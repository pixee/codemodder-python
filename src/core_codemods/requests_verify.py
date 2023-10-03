from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import SemgrepCodemod


class RequestsVerify(SemgrepCodemod):
    NAME = "requests-verify"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW
    SUMMARY = "Verify SSL certificates when making requests."
    DESCRIPTION = (
        "Makes any calls to requests.{func} with `verify=False` to `verify=True`"
    )

    @classmethod
    def rule(cls):
        return """
        rules:
          - patterns:
            - pattern: requests.$F(..., verify=False, ...)
            - pattern-inside: |
                import requests
                ...
        """

    def on_result_found(self, original_node, updated_node):
        new_args = self.replace_args(original_node, [("verify", "True", False)])
        return self.update_arg_target(updated_node, new_args)
