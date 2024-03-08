import pytest

from codemodder.codemods.test import BaseCodemodTest
from core_codemods.fix_dataclass_defaults import FixDataclassDefaults


class TestFixDataclassDefaults(BaseCodemodTest):
    codemod = FixDataclassDefaults

    def test_name(self):
        assert self.codemod.name == "fix-dataclass-defaults"

    def test_import(self, tmpdir):
        input_code = """
        import dataclass
    
        @dataclass.dataclass
        class Test:
            name: str = ""
            phones: list = []
            friends: dict = {} # I collect friends as I go :)
            family: set = set()
        """
        expected = """
        import dataclass
        from dataclass import field
    
        @dataclass.dataclass
        class Test:
            name: str = ""
            phones: list = field(default_factory=list)
            friends: dict = field(default_factory=dict) # I collect friends as I go :)
            family: set = field(default_factory=set)
        """
        self.run_and_assert(tmpdir, input_code, expected, num_changes=3)

    def test_import_from(self, tmpdir):
        input_code = """
        from dataclass import dataclass

        @dataclass
        class Test:
            name: str = ""
            phones: list = []
            friends: dict = {} # I collect friends as I go :)
            family: set = set()
        """
        expected = """
        from dataclass import field, dataclass

        @dataclass
        class Test:
            name: str = ""
            phones: list = field(default_factory=list)
            friends: dict = field(default_factory=dict) # I collect friends as I go :)
            family: set = field(default_factory=set)
        """
        self.run_and_assert(tmpdir, input_code, expected, num_changes=3)

    @pytest.mark.parametrize(
        "code",
        [
            """"
            from dataclasses import dataclass
            
            @dataclass
            class Test:
                name: str
                last = ""
                nums: list
                friends = []
                family = None
            """,
            """"
            from dataclasses import dataclass, field
        
            class Timer:
                pass

            @dataclass
            class Test:
                name: str
                last_name: str = None
                address: str = ""
                friends: tuple = ()
                nums: list[int] = field(default_factory=list)
                timer: Timer = field(default_factory=Timer)
                family: set = () # says set, actually a tuple
            """,
        ],
    )
    def test_no_change(self, tmpdir, code):
        self.run_and_assert(tmpdir, code, code)

    def test_exclude_line(self, tmpdir):
        input_code = (
            expected
        ) = """
        import dataclass
    
        @dataclass.dataclass
        class Test:
            phones: list = []
        """
        lines_to_exclude = [6]
        self.run_and_assert(
            tmpdir,
            input_code,
            expected,
            lines_to_exclude=lines_to_exclude,
        )
