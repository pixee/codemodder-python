import libcst as cst

from codemodder.codemods.utils_mixin import NameResolutionMixin
from core_codemods.api import Metadata, Reference, ReviewGuidance, SimpleCodemod


class FixDeprecatedAbstractproperty(SimpleCodemod, NameResolutionMixin):
    metadata = Metadata(
        name="fix-deprecated-abstractproperty",
        summary="Replace Deprecated `abc` Decorators",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[
            Reference(
                url="https://docs.python.org/3/library/abc.html#abc.abstractproperty"
            ),
            Reference(
                url="https://docs.python.org/3/library/abc.html#abc.abstractclassmethod"
            ),
            Reference(
                url="https://docs.python.org/3/library/abc.html#abc.abstractstaticmethod"
            ),
        ],
    )
    change_description = "Replace deprecated `abc` decorator."
    DEPRECATED_TO_NEW = {
        "abc.abstractproperty": "property",
        "abc.abstractclassmethod": "classmethod",
        "abc.abstractstaticmethod": "staticmethod",
    }

    def leave_Decorator(
        self, original_node: cst.Decorator, updated_node: cst.Decorator
    ):
        if not self.filter_by_path_includes_or_excludes(
            self.node_position(original_node)
        ):
            return updated_node

        if (
            base_name := self.find_base_name(original_node.decorator)
        ) in self.DEPRECATED_TO_NEW:
            self.add_needed_import("abc")
            self.remove_unused_import(original_node)
            self.report_change(original_node)
            return cst.FlattenSentinel(
                [
                    cst.Decorator(
                        decorator=cst.Name(value=self._new_decorator(base_name)),
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

    def _new_decorator(self, old_name: str) -> str:
        return self.DEPRECATED_TO_NEW[old_name]
