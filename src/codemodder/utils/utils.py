import libcst as cst


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
