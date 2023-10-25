import libcst as cst


def clean_simplestring(node: cst.SimpleString | str) -> str:
    if isinstance(node, str):
        return node.strip('"')
    return node.raw_value
