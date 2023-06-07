import libcst as cst
from libcst import matchers
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand
from .helper import split_module
from codemodder.codemods.base_codemod import BaseCodemod


replacement_import = "import secrets"
replacement_random_code = """secrets.SystemRandom()
gen = secrets.SystemRandom()
gen.uniform(0, 1)
"""


class SecureRandom(BaseCodemod, VisitorBasedCodemodCommand):
    NAME = "secure-random"
    DESCRIPTION = "Replaces random.{func} with more secure secrets library functions."

    def __init__(self, context: CodemodContext):
        self.random_func_called = False
        self.randint_func_called = False
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

        if self.random_func_called:
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

        if self.randint_func_called:
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
                                attr=cst.Name(value="randint"),
                            ),
                            args=[
                                cst.Arg(value=cst.Integer(value="0")),
                                cst.Arg(
                                    value=cst.Integer(value="10"),
                                ),
                            ],
                        )
                    ),
                ]
            )
            new_code = [first_line, second_line]
            statements_after_imports = new_code + statements_after_imports

        add_import = (
            [
                cst.parse_statement(
                    replacement_import, config=updated_node.config_for_parsing
                ),
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
            ]
            if self.random_func_called or self.randint_func_called
            else []
        )
        return updated_node.with_changes(
            body=[
                *statements_before_imports,
                *statements_until_add_imports,
                *add_import,
                *statements_after_imports,
            ]
        )

    def leave_Expr(self, original_node: cst.Expr, updated_node: cst.Expr) -> cst.Expr:
        if is_random_node(original_node):
            self.random_func_called = True
            return cst.RemoveFromParent()

        if is_randint_node(original_node):
            self.randint_func_called = True
            return cst.RemoveFromParent()
        return updated_node


def is_random_node(node: cst.Expr) -> bool:
    """
    Check to see if either: random.random() or random() is called.

    :param node:
    :return: bool
    """
    library_dot_random = matchers.Expr(
        value=matchers.Call(
            func=matchers.Attribute(
                value=matchers.Name(value="random"), attr=matchers.Name(value="random")
            )
        )
    )
    direct_random = matchers.Expr(
        value=matchers.Call(func=matchers.Name(value="random"))
    )

    return matchers.matches(
        node,
        matchers.OneOf(library_dot_random, direct_random),
    )


def is_randint_node(node: cst.Expr) -> bool:
    """
    Check to see if either: random.randint() or randint() is called.

    :param node:
    :return: bool
    """

    library_dot_randint = matchers.Expr(
        value=matchers.Call(
            func=matchers.Attribute(
                value=matchers.Name(value="random"), attr=matchers.Name(value="randint")
            )
        )
    )
    direct_randint = matchers.Expr(
        value=matchers.Call(func=matchers.Name(value="randint"))
    )

    return matchers.matches(
        node,
        matchers.OneOf(library_dot_randint, direct_randint),
    )


def is_random_import(node: cst.Import | cst.ImportFrom) -> bool:
    import_alias_random = matchers.ImportAlias(name=matchers.Name(value="random"))
    import_alias_randint = matchers.ImportAlias(name=matchers.Name(value="randint"))
    direct_import = matchers.Import(names=[import_alias_random])
    from_random_import_random = matchers.ImportFrom(
        module=cst.Name(value="random"), names=[import_alias_random]
    )
    from_random_import_randint = matchers.ImportFrom(
        module=cst.Name(value="random"), names=[import_alias_randint]
    )

    return matchers.matches(
        node,
        matchers.OneOf(
            direct_import, from_random_import_random, from_random_import_randint
        ),
    )
