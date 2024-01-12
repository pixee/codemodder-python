import libcst as cst

from codemodder.codemods.api import BaseCodemod, ReviewGuidance
from codemodder.codemods.utils_mixin import NameResolutionMixin


class UseGenerator(BaseCodemod, NameResolutionMixin):
    NAME = "use-generator"
    SUMMARY = "Use Generator Expressions Instead of List Comprehensions"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    DESCRIPTION = "Replace list comprehension with generator expression"
    REFERENCES = [
        {
            "url": "https://pylint.readthedocs.io/en/latest/user_guide/messages/refactor/use-a-generator.html",
            "description": "",
        },
        {
            "url": "https://docs.python.org/3/glossary.html#term-generator-expression",
            "description": "",
        },
        {
            "url": "https://docs.python.org/3/glossary.html#term-list-comprehension",
            "description": "",
        },
    ]

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call):
        if not self.filter_by_path_includes_or_excludes(
            self.node_position(original_node)
        ):
            return updated_node

        match original_node.func:
            # NOTE: could also support things like `list` and `tuple`
            # but it's a less compelling use case
            case cst.Name("any" | "all" | "sum" | "min" | "max"):
                if self.is_builtin_function(original_node):
                    match original_node.args[0].value:
                        case cst.ListComp(elt=elt, for_in=for_in):
                            self.add_change(original_node, self.CHANGE_DESCRIPTION)
                            return updated_node.with_changes(
                                args=[
                                    cst.Arg(
                                        value=cst.GeneratorExp(
                                            elt=elt,  # type: ignore
                                            for_in=for_in,  # type: ignore
                                            # No parens necessary since they are
                                            # already included by the call expr itself
                                            lpar=[],
                                            rpar=[],
                                        )
                                    )
                                ],
                            )

        return original_node
