from codemodder.codemods.libcst_transformer import NewArg
from core_codemods.api import (
    Metadata,
    Reference,
    ReviewGuidance,
    SimpleCodemod,
)


class EnableJinja2Autoescape(SimpleCodemod):
    metadata = Metadata(
        name="enable-jinja2-autoescape",
        summary="Enable Jinja2 Autoescape",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[
            Reference(url="https://owasp.org/www-community/attacks/xss/"),
            Reference(
                url="https://jinja.palletsprojects.com/en/3.1.x/api/#autoescaping"
            ),
        ],
    )
    change_description = (
        "Sets the `autoescape` parameter in jinja2.Environment to `True`."
    )
    detector_pattern = """
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
