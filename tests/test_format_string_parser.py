from typing import cast

import libcst as cst

from codemodder.utils.format_string_parser import (
    PrintfStringExpression,
    expressions_from_replacements,
    extract_mapping_key,
    parse_formatted_string,
    parse_formatted_string_raw,
)


class TestFormatStringParser:

    def test_parse_string_raw(self):
        string = "1 %s 3 %(key)d 5"
        assert len(parse_formatted_string_raw(string)) == 5

    def test_key_extraction(self):
        dict_key = "%(key)s"
        no_key = "%s"
        assert extract_mapping_key(dict_key) == "key"
        assert extract_mapping_key(no_key) is None

    def test_parsing_multiple_parts_mix_expressions(self):
        first = cst.parse_expression("'some %s'")
        first = cast(cst.SimpleString, first)
        second = cst.parse_expression("name")
        second = cast(cst.FormattedString, second)
        third = cst.parse_expression("'another %s'")
        third = cast(cst.SimpleString, third)
        keys = cst.parse_expression("(1,2,3,)")
        keys = cast(cst.Tuple, keys)
        parsed_keys = expressions_from_replacements(keys)
        all_parts = [first, second, third]
        parsed = parse_formatted_string(all_parts, parsed_keys)
        assert parsed and len(parsed) == 5

    def test_parsing_multiple_parts_values(self):
        first = cst.parse_expression("'some %(name)s'")
        first = cast(cst.SimpleString, first)
        second = cst.parse_expression("f' and %(phone)d'")
        second = cast(cst.FormattedString, second)
        all_parts = [first, *second.parts]
        key_dict: dict[str | cst.BaseExpression, cst.BaseExpression] = {
            "name": cst.parse_expression("name"),
            "phone": cst.parse_expression("phone"),
        }
        parsed = parse_formatted_string(all_parts, key_dict)
        assert parsed is not None
        values = [p.value for p in parsed]
        assert values == ["some ", "%(name)s", " and ", "%(phone)d"]

    def test_single_key_to_expression(self):
        first = cst.parse_expression("'%d'")
        first = cast(cst.SimpleString, first)
        keys = cst.parse_expression("1")
        parsed_keys = expressions_from_replacements(keys)
        parsed = parse_formatted_string([first], parsed_keys)
        assert parsed
        for p in parsed:
            assert isinstance(p, PrintfStringExpression)
            assert isinstance(p.key, int)
            assert p.expression == parsed_keys[p.key]

    def test_tuple_key_to_expression(self):
        first = cst.parse_expression("'%d%d%d'")
        first = cast(cst.SimpleString, first)
        keys = cst.parse_expression("(1,2,3,)")
        keys = cast(cst.Tuple, keys)
        parsed_keys = expressions_from_replacements(keys)
        parsed = parse_formatted_string([first], parsed_keys)
        assert parsed
        for p in parsed:
            assert isinstance(p, PrintfStringExpression)
            assert isinstance(p.key, int)
            assert p.expression == parsed_keys[p.key]

    def test_dict_key_to_expression(self):
        first = cst.parse_expression("'%(one)d%(two)d%(three)d'")
        first = cast(cst.SimpleString, first)
        keys: dict[str | cst.BaseExpression, cst.BaseExpression] = {
            "one": cst.Integer("1"),
            "two": cst.Integer("2"),
            "three": cst.Integer("3"),
        }
        parsed = parse_formatted_string([first], keys)
        assert parsed
        for p in parsed:
            assert isinstance(p, PrintfStringExpression)
            assert isinstance(p.key, str)
            assert p.expression == keys[p.key]
