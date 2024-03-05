import mock

from codemodder.codemods.test import BaseCodemodTest
from codemodder.dependency import Fickling
from core_codemods.harden_pickle_load import HardenPickleLoad


@mock.patch("codemodder.codemods.api.FileContext.add_dependency")
class TestHardenPickleLoad(BaseCodemodTest):
    codemod = HardenPickleLoad

    def test_pickle_import(self, add_dependency, tmpdir):
        original_code = """
        import pickle

        data = pickle.load(open('some.pickle', 'rb'))
        """

        new_code = """
        import fickling

        data = fickling.load(open('some.pickle', 'rb'))
        """

        self.run_and_assert(tmpdir, original_code, new_code)
        add_dependency.assert_called_once_with(Fickling)

    def test_pickle_import_alias(self, add_dependency, tmpdir):
        original_code = """
        import pickle as p

        data = p.load(open('some.pickle', 'rb'))
        """

        new_code = """
        import fickling

        data = fickling.load(open('some.pickle', 'rb'))
        """

        self.run_and_assert(tmpdir, original_code, new_code)
        add_dependency.assert_called_once_with(Fickling)

    def test_pickle_import_from(self, add_dependency, tmpdir):
        original_code = """
        from pickle import load

        data = load(open('some.pickle', 'rb'))
        """

        new_code = """
        import fickling

        data = fickling.load(open('some.pickle', 'rb'))
        """

        self.run_and_assert(tmpdir, original_code, new_code)
        add_dependency.assert_called_once_with(Fickling)

    def test_not_pickle_import(self, add_dependency, tmpdir):
        original_code = """
        import nickle

        data = nickle.load(open('some.pickle', 'rb'))
        """

        new_code = original_code

        self.run_and_assert(tmpdir, original_code, new_code)
        add_dependency.assert_not_called()

    def test_exclude_line(self, add_dependency, tmpdir):
        original_code = """
        import pickle

        pickle.load(open('some.pickle', 'rb'))
        """

        new_code = original_code

        self.run_and_assert(tmpdir, original_code, new_code, lines_to_exclude=[4])
        add_dependency.assert_not_called()

    def test_exclude_line_import_from(self, add_dependency, tmpdir):
        original_code = """
        from pickle import load

        load(open('some.pickle', 'rb'))
        """

        new_code = original_code

        self.run_and_assert(tmpdir, original_code, new_code, lines_to_exclude=[4])
        add_dependency.assert_not_called()
