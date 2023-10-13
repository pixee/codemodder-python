from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import SemgrepCodemod
from codemodder.codemods.api.helpers import NewArg


class EnableJinja2Autoescape(SemgrepCodemod):
    NAME = "enable-jinja2-autoescape"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW
    SUMMARY = "Enable jinja2 autoescape"
    DESCRIPTION = "Makes the `autoescape` parameter to jinja2.Environment be `True`."
    REFERENCES = [
        {"url": "https://owasp.org/www-community/attacks/xss/", "description": ""},
        {
            "url": "https://jinja.palletsprojects.com/en/3.1.x/api/#autoescaping",
            "description": "",
        },
    ]

    @classmethod
    def rule(cls):
        return """
            rules:
                - patterns:
                  - pattern: jinja2.Environment(...)
                  - pattern-not: jinja2.Environment(..., autoescape=True, ...)
                  - pattern-inside: |
                      import jinja2
                      ...
        """

    def on_result_found(self, original_node, updated_node):
        new_args = self.replace_args(
            original_node,
            [NewArg(name="autoescape", value="True", add_if_missing=True)],
        )
        return self.update_arg_target(updated_node, new_args)
