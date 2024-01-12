import libcst as cst

from codemodder.codemods.api import BaseCodemod, ReviewGuidance
from codemodder.codemods.utils_mixin import NameResolutionMixin


class FixDeprecatedAbstractproperty(BaseCodemod, NameResolutionMixin):
    NAME = "fix-deprecated-abstractproperty"
    SUMMARY = "Replace deprecated abstractproperty"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    DESCRIPTION = "Replace deprecated abstractproperty with property and abstractmethod"
    REFERENCES = [
        {
            "url": "https://docs.python.org/3/library/abc.html#abc.abstractproperty",
            "description": "",
        },
    ]

    def leave_Decorator(
        self, original_node: cst.Decorator, updated_node: cst.Decorator
    ):
        if not self.filter_by_path_includes_or_excludes(
            self.node_position(original_node)
        ):
            return updated_node

        if (
            base_name := self.find_base_name(original_node.decorator)
        ) and base_name == "abc.abstractproperty":
            self.add_needed_import("abc")
            self.remove_unused_import(original_node)
            self.add_change(original_node, self.DESCRIPTION)
            return cst.FlattenSentinel(
                [
                    cst.Decorator(
                        decorator=cst.Name(value="property"),
                        trailing_whitespace=updated_node.trailing_whitespace,
                    ),
                    cst.Decorator(
                        decorator=cst.Attribute(
                            value=cst.Name(value="abc"),
                            attr=cst.Name(value="abstractmethod"),
                        )
                    ),
                ]
            )

        return original_node
