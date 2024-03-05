import libcst as cst

from core_codemods.api import Metadata, Reference, ReviewGuidance, SimpleCodemod

default_limit = "5_000_000"


class LimitReadline(SimpleCodemod):
    metadata = Metadata(
        name="limit-readline",
        summary="Limit readline()",
        review_guidance=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
        references=[
            Reference(url="https://cwe.mitre.org/data/definitions/400.html"),
        ],
    )
    change_description = "Adds a size limit argument to readline() calls."
    detector_pattern = """
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
