from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import SemgrepCodemod
from codemodder.codemods.api.helpers import NewArg


class RequestsVerify(SemgrepCodemod):
    NAME = "requests-verify"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW
    SUMMARY = "Verify SSL Certificates for Requests."
    DESCRIPTION = (
        "Makes any calls to requests.{func} with `verify=False` to `verify=True`."
    )
    REFERENCES = [
        {"url": "https://requests.readthedocs.io/en/latest/api/", "description": ""},
        {
            "url": "https://owasp.org/www-community/attacks/Manipulator-in-the-middle_attack",
            "description": "",
        },
    ]

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
        new_args = self.replace_args(
            original_node, [NewArg(name="verify", value="True", add_if_missing=False)]
        )
        return self.update_arg_target(updated_node, new_args)
