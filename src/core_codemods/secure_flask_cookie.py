from core_codemods.api import Metadata, Reference, ReviewGuidance, SimpleCodemod
from core_codemods.secure_cookie_mixin import SecureCookieMixin


class SecureFlaskCookie(SimpleCodemod, SecureCookieMixin):
    metadata = Metadata(
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
        ],
    )
    change_description = "Flask response `set_cookie` call should be called with `secure=True`, `httponly=True`, and `samesite='Lax'`."
    detector_pattern = """
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

    def on_result_found(self, original_node, updated_node):
        new_args = self.replace_args(
            original_node, self._choose_new_args(original_node)
        )
        return self.update_arg_target(updated_node, new_args)
