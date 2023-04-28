import libcst as cst
import libcst.matchers as matchers
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand
from .helper import split_module


replacement_import = "import secrets"
replacement_random_code = """secrets.SystemRandom()
gen = secrets.SystemRandom()
gen.uniform(0, 1)
"""


class SecureRandom(VisitorBasedCodemodCommand):
    DESCRIPTION: str = (
        "Replaces random.{func} with more secure secrets library functions."
    )

    def __init__(self, context: CodemodContext):
        self.random_called = False
        super().__init__(context)

    def leave_Import(
        self, original_node: cst.Import, updated_node: cst.Import
    ) -> cst.Import:
        if is_random_import(original_node):
            return cst.RemoveFromParent()

        return updated_node

    def leave_ImportFrom(
        self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom
    ) -> cst.ImportFrom:
        if is_random_import(original_node):
            return cst.RemoveFromParent()

        return updated_node

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        (
            statements_before_imports,
            statements_until_add_imports,
            statements_after_imports,
        ) = split_module(original_node, updated_node)

        if self.random_called:
            first_line = cst.SimpleStatementLine(
                body=[
                    cst.Assign(
                        targets=[
                            cst.AssignTarget(
                                target=cst.Name(
                                    value="gen",
                                ),
                            ),
                        ],
                        value=cst.Call(
                            func=cst.Attribute(
                                value=cst.Name(
                                    value="secrets",
                                ),
                                attr=cst.Name(
                                    value="SystemRandom",
                                ),
                            ),
                        ),
                    )
                ]
            )

            second_line = cst.SimpleStatementLine(
                body=[
                    cst.Expr(
                        value=cst.Call(
                            func=cst.Attribute(
                                value=cst.Name(value="gen"),
                                attr=cst.Name(value="uniform"),
                            ),
                            args=[
                                cst.Arg(value=cst.Integer(value="0")),
                                cst.Arg(
                                    value=cst.Integer(value="1"),
                                ),
                            ],
                        )
                    ),
                ]
            )
            new_code = [first_line, second_line]
            statements_after_imports = new_code + statements_after_imports

        return updated_node.with_changes(
            body=[
                *statements_before_imports,
                *statements_until_add_imports,
                *[
                    cst.parse_statement(
                        replacement_import, config=updated_node.config_for_parsing
                    )
                ],
                cst.EmptyLine(
                    indent=True,
                    whitespace=cst.SimpleWhitespace(
                        value="",
                    ),
                    comment=None,
                    newline=cst.Newline(
                        value=None,
                    ),
                ),
                *statements_after_imports,
            ]
        )

    def leave_Expr(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        if is_random_node(original_node):
            self.random_called = True
            return cst.RemoveFromParent()
        return updated_node

    # def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
    #     if is_random_node(original_node):
    #         breakpoint()
    #         return updated_node.with_changes(func=cst.Name("secrets.SystemRandom()"))
    #     return updated_node


def is_random_node(node: cst.Expr) -> bool:

    library_dot_random = matchers.Expr(
        value=matchers.Call(
            func=matchers.Attribute(value=matchers.Name(value="random"))
        )
    )
    direct_random = matchers.Expr(
        value=matchers.Call(func=matchers.Name(value="random"))
    )

    return matchers.matches(
        node,
        matchers.OneOf(library_dot_random, direct_random),
    )


def is_random_import(node: cst.Import | cst.ImportFrom) -> bool:
    import_alias = matchers.ImportAlias(name=matchers.Name(value="random"))
    direct_import = matchers.Import(names=[import_alias])
    import_from = matchers.ImportFrom(names=[import_alias])
    return matchers.matches(
        node,
        matchers.OneOf(direct_import, import_from),
    )
