import libcst as cst
from functools import cache


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
    if cls.__module__ == "builtins":
        return cls.__qualname__
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
