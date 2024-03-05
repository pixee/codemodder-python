from codemodder.codemods.test import BaseCodemodTest
from core_codemods.literal_or_new_object_identity import LiteralOrNewObjectIdentity


class TestLiteralOrNewObjectIdentity(BaseCodemodTest):
    codemod = LiteralOrNewObjectIdentity

    def test_name(self):
        assert self.codemod.name == "literal-or-new-object-identity"

    def test_list(self, tmpdir):
        input_code = """
        l is [1,2,3]
        """
        expected = """
        l == [1,2,3]
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_list_indirect(self, tmpdir):
        input_code = """
        some_list = [1,2,3]
        l is some_list
        """
        expected = """
        some_list = [1,2,3]
        l == some_list
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_list_lhs(self, tmpdir):
        input_code = """
        [1,2,3] is l
        """
        expected = """
        [1,2,3] == l
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_list_function(self, tmpdir):
        input_code = """
        l is list({1,2,3})
        """
        expected = """
        l == list({1,2,3})
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_dict(self, tmpdir):
        input_code = """
        l is {1:2}
        """
        expected = """
        l == {1:2}
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_dict_function(self, tmpdir):
        input_code = """
        l is dict({1,2,3})
        """
        expected = """
        l == dict({1,2,3})
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_tuple(self, tmpdir):
        input_code = """
        l is (1,2,3)
        """
        expected = """
        l == (1,2,3)
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_tuple_function(self, tmpdir):
        input_code = """
        l is tuple({1,2,3})
        """
        expected = """
        l == tuple({1,2,3})
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_set(self, tmpdir):
        input_code = """
        l is {1,2,3}
        """
        expected = """
        l == {1,2,3}
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_set_function(self, tmpdir):
        input_code = """
        l is set([1,2,3])
        """
        expected = """
        l == set([1,2,3])
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_int(self, tmpdir):
        input_code = """
        l is 1
        """
        expected = """
        l == 1
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_float(self, tmpdir):
        input_code = """
        l is 1.0
        """
        expected = """
        l == 1.0
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_imaginary(self, tmpdir):
        input_code = """
        l is 1j
        """
        expected = """
        l == 1j
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_str(self, tmpdir):
        input_code = """
        l is '1'
        """
        expected = """
        l == '1'
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_fstr(self, tmpdir):
        input_code = """
        l is f'1'
        """
        expected = """
        l == f'1'
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_concatenated_str(self, tmpdir):
        input_code = """
        l is '1' ',2'
        """
        expected = """
        l == '1' ',2'
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_negative(self, tmpdir):
        input_code = """
        l is not [1,2,3]
        """
        expected = """
        l != [1,2,3]
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_do_nothing(self, tmpdir):
        input_code = """
        l == [1,2,3]
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_do_nothing_negative(self, tmpdir):
        input_code = """
        l != [1,2,3]
        """
        self.run_and_assert(tmpdir, input_code, input_code)
