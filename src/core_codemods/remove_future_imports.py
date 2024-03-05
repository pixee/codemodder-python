import libcst as cst

from core_codemods.api import Metadata, Reference, ReviewGuidance, SimpleCodemod

DEPRECATED_NAMES = [
    "print_function",
    "unicode_literals",
    "division",
    "absolute_import",
    "generators",
    "nested_scopes",
    "with_statement",
    "generator_stop",
]
CURRENT_NAMES = [
    "annotations",
]


class RemoveFutureImports(SimpleCodemod):
    metadata = Metadata(
        name="remove-future-imports",
        summary="Remove deprecated `__future__` imports",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[
            Reference(url="https://docs.python.org/3/library/__future__.html"),
        ],
    )
    change_description = "Remove deprecated `__future__` imports"

    def leave_ImportFrom(
        self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom
    ):
        match original_node.module:
            case cst.Name(value="__future__"):
                match original_node.names:
                    case cst.ImportStar():
                        names = [
                            cst.ImportAlias(name=cst.Name(value=name))
                            for name in CURRENT_NAMES
                        ]
                        self.add_change(original_node, self.change_description)
                        return original_node.with_changes(names=names)

                updated_names: list[cst.ImportAlias] = [
                    name
                    for name in original_node.names
                    if name.name.value not in DEPRECATED_NAMES
                ]
                self.add_change(original_node, self.change_description)
                return (
                    updated_node.with_changes(names=updated_names)
                    if updated_names
                    else cst.RemoveFromParent()
                )

        return updated_node
