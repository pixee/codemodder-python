from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.codemods.semgrep import SemgrepRuleDetector
from codemodder.codemods.utils_mixin import NameResolutionMixin
from core_codemods.api import CoreCodemod, Metadata, Reference, ReviewGuidance


class TempfileMktempTransformer(LibcstResultTransformer, NameResolutionMixin):
    change_description = "Replaces `tempfile.mktemp` with `tempfile.mkstemp`."
    _module_name = "tempfile"

    def on_result_found(self, original_node, updated_node):
        maybe_name = self.get_aliased_prefix_name(original_node, self._module_name)
        if (maybe_name := maybe_name or self._module_name) == self._module_name:
            self.add_needed_import(self._module_name)
        self.remove_unused_import(original_node)
        return self.update_call_target(updated_node, maybe_name, "mkstemp")


TempfileMktemp = CoreCodemod(
    metadata=Metadata(
        name="secure-tempfile",
        summary="Upgrade and Secure Temp File Creation",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[
            Reference(
                url="https://docs.python.org/3/library/tempfile.html#tempfile.mktemp"
            ),
        ],
    ),
    detector=SemgrepRuleDetector(
        """
        rules:
          - patterns:
            - pattern: tempfile.mktemp(...)
            - pattern-inside: |
                import tempfile
                ...
        """
    ),
    transformer=LibcstTransformerPipeline(TempfileMktempTransformer),
)
