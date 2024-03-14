from functools import cache
from typing import Sequence

import libcst as cst


@cache
def list_subclasses(base_kls) -> set[str]:
    all_subclasses = set()
    stack = [base_kls]
    while stack:
        kls = stack.pop()
        all_subclasses.add(kls)
        stack.extend(kls.__subclasses__())
    return all_subclasses


def full_qualified_name_from_class(cls) -> str:
    return f"{cls.__module__}.{cls.__qualname__}"


def clean_simplestring(node: cst.SimpleString | str) -> str:
    if isinstance(node, str):
        return node.strip('"')
    return node.raw_value


def true_value(node: cst.Name | cst.SimpleString) -> str | int | bool:
    match node:
        case cst.SimpleString():
            return clean_simplestring(node)
        case cst.Name():
            val = node.value
            if val.lower() == "true":
                return True
            elif val.lower() == "false":
                return False
            return val
    return ""


def extract_targets_of_assignment(
    assignment: cst.AnnAssign | cst.Assign | cst.WithItem | cst.NamedExpr,
) -> list[cst.BaseExpression]:
    match assignment:
        case cst.AnnAssign():
            if assignment.target:
                return [assignment.target]
        case cst.Assign():
            return [t.target for t in assignment.targets]
        case cst.NamedExpr():
            return [assignment.target]
        case cst.WithItem():
            if assignment.asname:
                return [assignment.asname.name]
    return []


def positional_to_keyword(
    args: Sequence[cst.Arg], pos_to_keyword: list[str | None]
) -> list[cst.Arg]:
    """
    Given a sequence of Args, converts all the positional arguments into keyword arguments according to a given map.
    """
    new_args = []
    for i, arg in enumerate(args):
        if arg.keyword is None and pos_to_keyword[i] is not None:
            new_args.append(arg.with_changes(keyword=cst.Name(pos_to_keyword[i])))
        else:
            new_args.append(arg)
    return new_args


def is_empty_string_literal(node) -> bool:
    match node:
        case cst.SimpleString() if node.raw_value == "":
            return True
        case cst.FormattedString() if not node.parts:
            return True
    return False


def is_empty_sequence_literal(expr: cst.BaseExpression) -> bool:
    match expr:
        case cst.Dict() | cst.Tuple() if not expr.elements:
            return True
    return False
