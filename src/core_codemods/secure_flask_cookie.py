from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.codemods.semgrep import SemgrepRuleDetector
from core_codemods.api import Metadata, Reference, ReviewGuidance
from core_codemods.api.core_codemod import CoreCodemod
from core_codemods.secure_cookie_mixin import SecureCookieMixin


class SecureCookieTransformer(LibcstResultTransformer, SecureCookieMixin):
    change_description = "Flask response `set_cookie` call should be called with `secure=True`, `httponly=True`, and `samesite='Lax'`."

    def on_result_found(self, original_node, updated_node):
        new_args = self.replace_args(
            original_node, self._choose_new_args(original_node)
        )
        return self.update_arg_target(updated_node, new_args)


SecureFlaskCookie = CoreCodemod(
    metadata=Metadata(
        name="secure-flask-cookie",
        summary="Use Safe Parameters in `flask` Response `set_cookie` Call",
        review_guidance=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
        references=[
            Reference(
                url="https://flask.palletsprojects.com/en/3.0.x/api/#flask.Response.set_cookie"
            ),
            Reference(
                url="https://owasp.org/www-community/controls/SecureCookieAttribute"
            ),
            Reference(url="https://cwe.mitre.org/data/definitions/1004"),
            Reference(url="https://cwe.mitre.org/data/definitions/311"),
            Reference(url="https://cwe.mitre.org/data/definitions/315"),
            Reference(url="https://cwe.mitre.org/data/definitions/614"),
        ],
    ),
    detector=SemgrepRuleDetector(
        """
        rules:
          - id: secure-flask-cookie
            mode: taint
            pattern-sources:
              - pattern-either:
                  - patterns:
                    - pattern: flask.make_response(...)
                    - pattern-inside: |
                        import flask
                        ...
                  - patterns:
                    - pattern: flask.Response(...)
                    - pattern-inside: |
                        import flask
                        ...
            pattern-sinks:
              - patterns:
                - pattern: $SINK.set_cookie(...)
                - pattern-not: $SINK.set_cookie(..., secure=True, ..., httponly=True, ..., samesite="Lax", ...)
                - pattern-not: $SINK.set_cookie(..., secure=True, ..., httponly=True, ..., samesite="Strict", ...)
    """
    ),
    transformer=LibcstTransformerPipeline(SecureCookieTransformer),
)
