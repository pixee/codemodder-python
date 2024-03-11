import pytest

from codemodder.codemods.test import BaseCodemodTest
from core_codemods.fix_missing_self_or_cls import FixMissingSelfOrCls


class TestFixMissingSelfOrCls(BaseCodemodTest):
    codemod = FixMissingSelfOrCls

    def test_name(self):
        assert self.codemod.name == "fix-missing-self-or-cls"

    def test_change(self, tmpdir):
        input_code = """
        class A:
            def method():
                pass
            
            @classmethod
            def clsmethod():
                pass

            def __new__():
                pass
            def __init_subclass__():
                pass
        """
        expected = """
        class A:
            def method(self):
                pass
            
            @classmethod
            def clsmethod(cls):
                pass

            def __new__(cls):
                pass
            def __init_subclass__(cls):
                pass
        """
        self.run_and_assert(tmpdir, input_code, expected, num_changes=4)

    @pytest.mark.parametrize(
        "code",
        [
            """
            def my_function():
                pass
            """,
            """
            class A:
                def method(self, arg):
                    pass

                @classmethod
                def clsmethod(cls, arg):
                    pass
                    
                @staticmethod
                def my_static():
                    pass
            """,
            """
            class MyBaseClass:
                def __new__(*args, **kwargs):
                    pass
                def __init_subclass__(**kwargs):
                    pass
            """,
        ],
    )
    def test_no_change(self, tmpdir, code):
        self.run_and_assert(tmpdir, code, code)

    def test_with_args_no_change(self, tmpdir):
        input_code = """
        class A:
            def method(one, two):
               pass

            def method(*args, two=2):
               pass
               
            def method(**kwargs):
               pass
                                  
            @classmethod
            def clsmethod(one, two):
               pass
        
            @classmethod
            def kls(**kwargs):
               pass
           """
        self.run_and_assert(tmpdir, input_code, input_code)

    # def test_exclude_line(self, tmpdir):
    #     input_code = (
    #         expected
    #     ) = """
    #     assert (1, 2)
    #     """
    #     lines_to_exclude = [2]
    #     self.run_and_assert(
    #         tmpdir,
    #         input_code,
    #         expected,
    #         lines_to_exclude=lines_to_exclude,
    #     )
