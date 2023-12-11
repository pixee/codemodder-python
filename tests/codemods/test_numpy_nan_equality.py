from core_codemods.numpy_nan_equality import NumpyNanEquality
from tests.codemods.base_codemod_test import BaseCodemodTest
from textwrap import dedent


class TestNumpyNanEquality(BaseCodemodTest):
    codemod = NumpyNanEquality

    def test_name(self):
        assert self.codemod.name() == "numpy-nan-equality"

    def test_simple(self, tmpdir):
        input_code = """\
        import numpy
        if a == numpy.nan:
            pass
        """
        expected = """\
        import numpy
        if numpy.isnan(a):
            pass
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_simple_inequality(self, tmpdir):
        input_code = """\
        import numpy
        if a != numpy.nan:
            pass
        """
        expected = """\
        import numpy
        if not numpy.isnan(a):
            pass
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_simple_inequality_2(self, tmpdir):
        input_code = """\
        import numpy
        if not (a != numpy.nan):
            pass
        """
        expected = """\
        import numpy
        if not (not numpy.isnan(a)):
            pass
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_simple_parenthesis(self, tmpdir):
        input_code = """\
        import numpy
        if (  a == numpy.nan  ):
            pass
        """
        expected = """\
        import numpy
        if (  numpy.isnan(a)  ):
            pass
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_conjunction(self, tmpdir):
        input_code = """\
        import numpy
        if a != numpy.nan and b!= numpy.nan:
            pass
        """
        expected = """\
        import numpy
        if not numpy.isnan(a) and not numpy.isnan(b):
            pass
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 2

    def test_from_numpy(self, tmpdir):
        input_code = """\
        from numpy import nan
        if a == nan:
            pass
        """
        expected = """\
        import numpy

        if numpy.isnan(a):
            pass
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_simple_left(self, tmpdir):
        input_code = """\
        import numpy
        if numpy.nan == a:
            pass
        """
        expected = """\
        import numpy
        if numpy.isnan(a):
            pass
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_alias(self, tmpdir):
        input_code = """\
        import numpy as np
        if a == np.nan:
            pass
        """
        expected = """\
        import numpy as np
        if np.isnan(a):
            pass
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_multiple_comparisons(self, tmpdir):
        input_code = """\
        import numpy as np
        if a == np.nan == b == c == d <= e:
            pass
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0

    def test_not_numpy(self, tmpdir):
        input_code = """\
        import not_numpy as np
        if a == np.nan:
            pass
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0

    def test_numpy_other_operator(self, tmpdir):
        input_code = """\
        import numpy
        if a <= numpy.nan:
            pass
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0
