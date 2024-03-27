from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.fix_dataclass_defaults import FixDataclassDefaults


class TestFixDataclassDefaults(BaseIntegrationTest):
    codemod = FixDataclassDefaults
    original_code = """
    from dataclasses import dataclass

    @dataclass
    class Test:
        name: str = ""
        phones: list = []
        friends: dict = {}
        family: set = set()
    """
    replacement_lines = [
        (1, """from dataclasses import field, dataclass\n"""),
        (6, """    phones: list = field(default_factory=list)\n"""),
        (7, """    friends: dict = field(default_factory=dict)\n"""),
        (8, """    family: set = field(default_factory=set)\n"""),
    ]
    # fmt: off
    expected_diff = (
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
