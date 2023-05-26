# split_module is 'borrowed' from libcst.codemod.visitors._add_imports.py

from libcst import matchers as m
from libcst import (
    SimpleStatementLine,
    BaseCompoundStatement,
    Module,
)
from typing import List, Tuple, Union

all_imports = []


def split_module(
    orig_module: Module, updated_module: Module
) -> Tuple[
    List[Union[SimpleStatementLine, BaseCompoundStatement]],
    List[Union[SimpleStatementLine, BaseCompoundStatement]],
    List[Union[SimpleStatementLine, BaseCompoundStatement]],
]:
    statement_before_import_location = 0
    import_add_location = 0

    # never insert an import before initial __strict__ flag
    if m.matches(
        orig_module,
        m.Module(
            body=[
                m.SimpleStatementLine(
                    body=[
                        m.Assign(targets=[m.AssignTarget(target=m.Name("__strict__"))])
                    ]
                ),
                m.ZeroOrMore(),
            ]
        ),
    ):
        statement_before_import_location = import_add_location = 1

    # This works under the principle that while we might modify node contents,
    # we have yet to modify the number of statements. So we can match on the
    # original tree but break up the statements of the modified tree. If we
    # change this assumption in this visitor, we will have to change this code.
    for i, statement in enumerate(orig_module.body):
        if m.matches(
            statement, m.SimpleStatementLine(body=[m.Expr(value=m.SimpleString())])
        ):
            statement_before_import_location = import_add_location = 1
        elif isinstance(statement, SimpleStatementLine):
            for possible_import in statement.body:
                for last_import in all_imports:
                    if possible_import is last_import:
                        import_add_location = i + 1
                        break

    return (
        list(updated_module.body[:statement_before_import_location]),
        list(updated_module.body[statement_before_import_location:import_add_location]),
        list(updated_module.body[import_add_location:]),
    )
