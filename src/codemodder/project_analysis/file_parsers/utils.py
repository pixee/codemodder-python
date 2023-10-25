import libcst as cst


def clean_simplestring(node: cst.SimpleString) -> str:
    return node.value.strip('"')
