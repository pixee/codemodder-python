# pylint: disable=redefined-outer-name
import pytest

from codemodder.code_directory import match_files


@pytest.fixture(scope="module")
def dir_structure(tmp_path_factory):
    tests_dir = tmp_path_factory.mktemp("tests")
    samples_dir = tests_dir / "samples"
    samples_dir.mkdir()
    (samples_dir / "make_request.py").touch()
    (samples_dir / "insecure_random.py").touch()

    more_samples_dir = samples_dir / "more_samples"
    more_samples_dir.mkdir()
    (more_samples_dir / "empty_for_testing.py").touch()
    (more_samples_dir / "empty_for_testing.txt").touch()

    assert len(list(tests_dir.rglob("*"))) == 6

    return tests_dir


class TestMatchFiles:
    def _assert_expected(self, result_files, expected_files):
        assert len(result_files) == len(expected_files)
        file_names = [file.name for file in result_files]
        file_names.sort()
        assert file_names == expected_files

    def test_all_py_files_match(self, dir_structure):
        expected = ["empty_for_testing.py", "insecure_random.py", "make_request.py"]
        files = match_files(dir_structure)
        self._assert_expected(files, expected)

    def test_match_excluded(self, dir_structure):
        expected = ["empty_for_testing.py", "insecure_random.py"]
        files = match_files(dir_structure, ["*request.py"])
        self._assert_expected(files, expected)

    def test_match_excluded_dir_incorrect_glob(self, dir_structure):
        incorrect_glob = "more_samples"
        expected = ["empty_for_testing.py", "insecure_random.py", "make_request.py"]
        files = match_files(dir_structure, [incorrect_glob])
        self._assert_expected(files, expected)

    def test_match_excluded_dir_correct_glob(self, dir_structure):
        correct_globs = ["**/more_samples/**", "*/more_samples/*"]
        for correct_glob in correct_globs:
            expected = ["insecure_random.py", "make_request.py"]
            files = match_files(dir_structure, [correct_glob])
            self._assert_expected(files, expected)

    def test_match_excluded_multiple(self, dir_structure):
        expected = ["insecure_random.py"]
        files = match_files(dir_structure, ["*request.py", "*empty*"])
        self._assert_expected(files, expected)

    def test_match_included(self, dir_structure):
        expected = ["make_request.py"]
        files = match_files(dir_structure, include_paths=["*request.py"])
        self._assert_expected(files, expected)

    def test_match_excluded_precedence_over_included(self, dir_structure):
        expected = ["empty_for_testing.py", "insecure_random.py"]
        files = match_files(
            dir_structure,
            exclude_paths=["*request.py"],
            include_paths=["*request.py", "*empty*.py", "*random.py"],
        )
        self._assert_expected(files, expected)
