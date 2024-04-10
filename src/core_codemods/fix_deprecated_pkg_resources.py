import libcst as cst

from codemodder.codemods.utils_mixin import NameResolutionMixin
from core_codemods.api import Metadata, Reference, ReviewGuidance, SimpleCodemod


class FixDeprecatedPkgResources(SimpleCodemod, NameResolutionMixin):
    metadata = Metadata(
        name="fix-deprecated-pkg-resources",
        summary="Replace Deprecated Use of `pkg_resources` Module`",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[
            Reference(
                url="TODOOOOhttps://docs.python.org/3/library/logging.html#logging.Logger.warning"
            ),
        ],
    )
    change_description = "Replace deprecated `logging.warn` with `logging.warning`"
    detector_pattern = f"""
        rules:
          - id: {metadata.name}
            pattern: pkg_resources.get_distribution(...)
            pattern-inside: |
              import pkg_resources
              ...
        """

    def on_result_found(self, original_node, updated_node):
        self.remove_unused_import(original_node)
        self.add_needed_import("importlib.metadata", "distribution")
        return updated_node.with_changes(func=cst.Name(value="distribution"))
