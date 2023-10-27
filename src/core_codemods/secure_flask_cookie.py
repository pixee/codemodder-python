from libcst import matchers
from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import SemgrepCodemod
from codemodder.codemods.api.helpers import NewArg


class SecureFlaskCookie(SemgrepCodemod):
    NAME = "secure-flask-cookie"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW
    SUMMARY = "Use Safe Parameters in `flask` Response `set_cookie` Call"
    DESCRIPTION = "Flask response `set_cookie` call should be called with `secure=True`, `httponly=True`, and `samesite='Lax'`."
    REFERENCES = [
        {
            "url": "https://flask.palletsprojects.com/en/3.0.x/api/#flask.Response.set_cookie",
            "description": "",
        },
        {
            "url": "https://owasp.org/www-community/controls/SecureCookieAttribute",
            "description": "",
        },
    ]

    @classmethod
    def rule(cls):
        return """
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

    def _choose_new_args(self, original_node):
        new_args = [
            NewArg(name="secure", value="True", add_if_missing=True),
            NewArg(name="httponly", value="True", add_if_missing=True),
        ]

        samesite = matchers.Arg(
            keyword=matchers.Name(value="samesite"),
            value=matchers.SimpleString(value="'Strict'"),
        )

        # samesite=Strict is OK because it's more restrictive than Lax.
        strict_samesite_defined = any(
            matchers.matches(arg, samesite) for arg in original_node.args
        )
        if not strict_samesite_defined:
            new_args.append(
                NewArg(name="samesite", value="'Lax'", add_if_missing=True),
            )

        return new_args

    def on_result_found(self, original_node, updated_node):
        new_args = self.replace_args(
            original_node, self._choose_new_args(original_node)
        )
        return self.update_arg_target(updated_node, new_args)
