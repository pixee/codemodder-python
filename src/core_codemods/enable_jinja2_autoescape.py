from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
    NewArg,
)
from codemodder.codemods.semgrep import SemgrepRuleDetector
from core_codemods.api import CoreCodemod, Metadata, Reference, ReviewGuidance


class EnableJinja2AutoescapeTransformer(LibcstResultTransformer):
    change_description = (
        "Sets the `autoescape` parameter in jinja2.Environment to `True`."
    )

    def on_result_found(self, original_node, updated_node):
        new_args = self.replace_args(
            original_node,
            [NewArg(name="autoescape", value="True", add_if_missing=True)],
        )
        return self.update_arg_target(updated_node, new_args)


EnableJinja2Autoescape = CoreCodemod(
    metadata=Metadata(
        name="enable-jinja2-autoescape",
        summary="Enable Jinja2 Autoescape",
        review_guidance=ReviewGuidance.MERGE_AFTER_REVIEW,
        references=[
            Reference(url="https://owasp.org/www-community/attacks/xss/"),
            Reference(
                url="https://jinja.palletsprojects.com/en/3.1.x/api/#autoescaping"
            ),
        ],
    ),
    detector=SemgrepRuleDetector(
        """
            rules:
              - pattern-either:
                - patterns:
                  - pattern: jinja2.Environment(...)
                  - pattern-not: jinja2.Environment(..., autoescape=True, ...)
                  - pattern-not: jinja2.Environment(..., autoescape=jinja2.select_autoescape(...), ...)
                  # Exclude cases where the arguments can't be precisely determined
                  - pattern-not: jinja2.Environment(**$KWARGS)
                  - pattern-inside: |
                      import jinja2
                      ...
                - patterns:
                  - pattern: aiohttp_jinja2.setup(..., autoescape=False, ...)
                  - pattern-inside: |
                      import aiohttp_jinja2
                      ...
        """
    ),
    transformer=LibcstTransformerPipeline(EnableJinja2AutoescapeTransformer),
)
