from codemodder.codemods.test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)
from core_codemods.fix_dataclass_defaults import FixDataclassDefaults


class TestFixDataclassDefaults(BaseIntegrationTest):
    codemod = FixDataclassDefaults
    code_path = "tests/samples/fix_dataclass_defaults.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (0, """from dataclasses import field, dataclass\n"""),
            (5, """    phones: list = field(default_factory=list)\n"""),
            (6, """    friends: dict = field(default_factory=dict)\n"""),
            (7, """    family: set = field(default_factory=set)\n"""),
        ],
    )

    # fmt: off
    expected_diff =(
    """--- \n"""
    """+++ \n"""
    """@@ -1,8 +1,8 @@\n"""
    """-from dataclasses import dataclass\n"""
    """+from dataclasses import field, dataclass\n"""
    """ \n"""
    """ @dataclass\n"""
    """ class Test:\n"""
    """     name: str = ""\n"""
    """-    phones: list = []\n"""
    """-    friends: dict = {}\n"""
    """-    family: set = set()\n"""
    """+    phones: list = field(default_factory=list)\n"""
    """+    friends: dict = field(default_factory=dict)\n"""
    """+    family: set = field(default_factory=set)\n"""
    )
    # fmt: on

    expected_line_change = "6"
    change_description = FixDataclassDefaults.change_description
    num_changes = 3
