from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import SemgrepCodemod
from codemodder.codemods.api.helpers import NewArg


class EnableJinja2Autoescape(SemgrepCodemod):
    NAME = "enable-jinja2-autoescape"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    SUMMARY = "Enable Jinja2 Autoescape"
    DESCRIPTION = "Sets the `autoescape` parameter in jinja2.Environment to `True`."
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
              - pattern-either:
                - patterns:
                  - pattern: jinja2.Environment(...)
                  - pattern-not: jinja2.Environment(..., autoescape=True, ...)
                  - pattern-inside: |
                      import jinja2
                      ...
                - patterns:
                  - pattern: aiohttp_jinja2.setup(...)
                  - pattern-not: aiohttp_jinja2.setup(..., autoescape=True, ...)
                  - pattern-inside: |
                      import aiohttp_jinja2
                      ...
        """

    def on_result_found(self, original_node, updated_node):
        new_args = self.replace_args(
            original_node,
            [NewArg(name="autoescape", value="True", add_if_missing=True)],
        )
        return self.update_arg_target(updated_node, new_args)
