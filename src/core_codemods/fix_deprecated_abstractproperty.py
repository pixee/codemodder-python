import libcst as cst

from codemodder.codemods.utils_mixin import NameResolutionMixin
from core_codemods.api import Metadata, Reference, ReviewGuidance, SimpleCodemod


class FixDeprecatedAbstractproperty(SimpleCodemod, NameResolutionMixin):
    metadata = Metadata(
        name="fix-deprecated-abstractproperty",
        summary="Replace Deprecated `abstractproperty` or `abstractclassmethod` Decorators",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[
            Reference(
                url="https://docs.python.org/3/library/abc.html#abc.abstractproperty"
            ),
            Reference(
                url="https://docs.python.org/3/library/abc.html#abc.abstractclassmethod"
            ),
        ],
    )
    change_description = "Replace deprecated `abc` module decorator."

    def leave_Decorator(
        self, original_node: cst.Decorator, updated_node: cst.Decorator
    ):
        if not self.filter_by_path_includes_or_excludes(
            self.node_position(original_node)
        ):
            return updated_node

        if (base_name := self.find_base_name(original_node.decorator)) in (
            "abc.abstractproperty",
            "abc.abstractclassmethod",
        ):
            self.add_needed_import("abc")
            self.remove_unused_import(original_node)
            self.report_change(original_node)
            new_decorator = cst.Name(
                value=(
                    "property" if base_name == "abc.abstractproperty" else "classmethod"
                )
            )
            return cst.FlattenSentinel(
                [
                    cst.Decorator(
                        decorator=new_decorator,
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
