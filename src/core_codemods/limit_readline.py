import libcst as cst
from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import SemgrepCodemod


default_limit = "5_000_000"


class LimitReadline(SemgrepCodemod):
    NAME = "limit-readline"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW
    SUMMARY = "Limit readline()"
    DESCRIPTION = "Adds a size limit argument to readline() calls."
    REFERENCES = [
        {"url": "https://cwe.mitre.org/data/definitions/400.html", "description": ""}
    ]

    @classmethod
    def rule(cls):
        return """
        rules:
          - id: limit-readline
            mode: taint
            pattern-sources:
              - pattern-either:
                  - patterns:
                    - pattern: io.StringIO(...)
                    - pattern-inside: |
                        import io
                        ...
                  - patterns:
                    - pattern: io.BytesIO(...)
                    - pattern-inside: |
                        import io
                        ...
                  - pattern: open(...)
            pattern-sinks:
              - pattern: $SINK.readline()
        """

    def on_result_found(self, _, updated_node):
        return self.update_arg_target(updated_node, [cst.Integer(default_limit)])
