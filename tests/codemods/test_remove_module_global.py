from codemodder.codemods.test import BaseCodemodTest
from core_codemods.remove_module_global import RemoveModuleGlobal


class TestJwtDecodeVerify(BaseCodemodTest):
    codemod = RemoveModuleGlobal

    def test_name(self):
        assert self.codemod.name == "remove-module-global"

    def test_simple(self, tmpdir):
        input_code = """
        price = 25
        global price
        """
        expected = """
        price = 25
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_reassigned(self, tmpdir):
        input_code = """
        price = 25
        print("hello")
        global price
        price = 30
        """
        expected = """
        price = 25
        print("hello")
        price = 30
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_attr_call(self, tmpdir):
        input_code = """
        class Price:
            pass
        PRICE = Price()
        global PRICE
        PRICE.__repr__
        """
        expected = """
        class Price:
            pass
        PRICE = Price()
        PRICE.__repr__
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_correct_scope(self, tmpdir):
        input_code = """
        price = 25
        def change_price():
            global price
            price = 30
        """
        self.run_and_assert(tmpdir, input_code, input_code)
