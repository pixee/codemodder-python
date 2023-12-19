import libcst as cst

from codemodder.codemods.api import BaseCodemod, ReviewGuidance


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


class RemoveFutureImports(BaseCodemod):
    NAME = "remove-future-imports"
    SUMMARY = "Remove deprecated `__future__` imports"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    DESCRIPTION = "Remove deprecated `__future__` imports"
    REFERENCES = [
        {
            "url": "https://docs.python.org/3/library/__future__.html",
            "description": "",
        },
    ]

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
                        self.add_change(original_node, self.CHANGE_DESCRIPTION)
                        return original_node.with_changes(names=names)

                updated_names: list[cst.ImportAlias] = [
                    name
                    for name in original_node.names
                    if name.name.value not in DEPRECATED_NAMES
                ]
                self.add_change(original_node, self.CHANGE_DESCRIPTION)
                return (
                    updated_node.with_changes(names=updated_names)
                    if updated_names
                    else cst.RemoveFromParent()
                )

        return updated_node
