import re
from dataclasses import dataclass
from typing import TypeAlias

import libcst as cst


@dataclass(frozen=True)
class PrintfStringText:
    origin: cst.SimpleString | cst.FormattedStringText
    value: str
    index: int


@dataclass(frozen=True)
class PrintfStringExpression:
    origin: cst.SimpleString | cst.FormattedStringText
    expression: cst.BaseExpression
    key: str | int | None
    index: int
    value: str


# Type aliases
StringLiteralNodeType: TypeAlias = (
    cst.SimpleString | cst.FormattedStringText | PrintfStringText
)
ExpressionNodeType: TypeAlias = (
    cst.BaseExpression | cst.FormattedStringExpression | PrintfStringExpression
)

# regexes for parsing strings with format tokens
conversion_type = r"[diouxXeEfFgGcrsa%]"
mapping_key = r"\([^)]*\)"
conversion_flags = r"[#0\-+ ]*"
minimum_width = r"(?:\d+|\*)"
length_modifier = r"[hlL]"
param_regex = f"(%(?:{mapping_key})?{conversion_flags}{minimum_width}?{length_modifier}?{conversion_type})"
param_pattern = re.compile(param_regex)
mapping_key_pattern = re.compile(f"({mapping_key})")


def extract_mapping_key(string: str) -> str | None:
    # TODO extract all the flags and values into an object
    maybe_match = mapping_key_pattern.search(string)
    return maybe_match[0][1:-1] if maybe_match else None


def parse_formatted_string_raw(string: str) -> list[str]:
    return param_pattern.split(string)


def _convert_piece_and_parts(
    piece: cst.SimpleString | cst.FormattedStringText,
    piece_parts,
    token_count: int,
    keys: dict | list,
) -> (
    tuple[
        list[
            cst.SimpleString
            | cst.FormattedStringText
            | PrintfStringExpression
            | PrintfStringText
        ],
        int,
    ]
    | None
):
    # if it does not contain any %s token we maintain the original
    if _has_conversion_parts(piece_parts):
        parsed_parts: list[
            cst.SimpleString
            | cst.FormattedStringText
            | PrintfStringExpression
            | PrintfStringText
        ] = []
        index_count = 0
        for s in piece_parts:
            if s:
                if s.startswith("%"):
                    # TODO should account for different prefixes when key is extracted
                    key = extract_mapping_key(s)
                    match keys:
                        case dict():
                            key = extract_mapping_key(s)
                            if not key:
                                return None
                            parsed_parts.append(
                                PrintfStringExpression(
                                    origin=piece,
                                    expression=keys[key],
                                    key=key,
                                    index=index_count,
                                    value=s,
                                )
                            )
                        case list():
                            parsed_parts.append(
                                PrintfStringExpression(
                                    origin=piece,
                                    expression=keys[token_count],
                                    key=token_count,
                                    index=index_count,
                                    value=s,
                                )
                            )
                    token_count = token_count + 1
                else:
                    parsed_parts.append(
                        PrintfStringText(origin=piece, value=s, index=index_count)
                    )
                index_count += len(s)
        return parsed_parts, token_count
    return [piece], token_count


def expressions_from_replacements(
    replacements: cst.Tuple | cst.BaseExpression,
) -> list[cst.BaseExpression]:
    """
    Gather all the expressions from a tuple literal.
    """
    match replacements:
        case cst.Tuple():
            return [e.value for e in replacements.elements]
    return [replacements]


def dict_to_values_dict(
    expr_dict: dict[cst.BaseExpression, cst.BaseExpression]
) -> dict[str | cst.BaseExpression, cst.BaseExpression]:
    return {
        extract_raw_value(k): v
        for k, v in expr_dict.items()
        if isinstance(k, cst.SimpleString | cst.FormattedStringText)
    }


def parse_formatted_string(
    string_pieces: list[StringLiteralNodeType | ExpressionNodeType],
    keys: dict[str | cst.BaseExpression, cst.BaseExpression] | list[cst.BaseExpression],
) -> list[StringLiteralNodeType | ExpressionNodeType] | None:
    parts: list[StringLiteralNodeType | ExpressionNodeType] = []
    parsed_pieces: list[
        tuple[StringLiteralNodeType | ExpressionNodeType, list[str] | None]
    ] = []
    for piece in string_pieces:
        match piece:
            case cst.FormattedStringText() | cst.SimpleString():
                parsed_pieces.append(
                    (piece, parse_formatted_string_raw(extract_raw_value(piece)))
                )
            case _:
                parsed_pieces.append((piece, None))
    token_count = 0
    for piece, piece_parts in parsed_pieces:
        match piece:
            case cst.SimpleString() | cst.FormattedStringText():
                if maybe_conversion := _convert_piece_and_parts(
                    piece, piece_parts, token_count, keys
                ):
                    converted, token_count = maybe_conversion
                    parts.extend(converted)
                else:
                    return None
            case _:
                parts.append(piece)
    return parts


def _has_conversion_parts(piece_parts: list[str]) -> bool:
    return any(s.startswith("%") for s in piece_parts)


def extract_raw_value(
    node: cst.FormattedStringText | cst.SimpleString | PrintfStringText,
) -> str:
    match node:
        case cst.FormattedStringText():
            return node.value
        case cst.SimpleString():
            return node.raw_value
        case PrintfStringText():
            return node.value
    # shouldn't reach here
    return ""
