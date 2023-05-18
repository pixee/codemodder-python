from codemodder.code_directory import match_files


class TestMatchFiles:
    def _assert_expected(self, result_files, expected_files):
        assert len(result_files) == len(expected_files)
        file_names = [file.name for file in result_files]
        file_names.sort()
        assert file_names == expected_files

    def test_all_py_files_match(self):
        expected = ["empty_for_testing.py", "insecure_random.py", "make_request.py"]
        files = match_files("tests/samples/")
        self._assert_expected(files, expected)

    def test_match_excluded(self):
        expected = ["empty_for_testing.py", "insecure_random.py"]
        files = match_files("tests/samples/", "*request.py")
        self._assert_expected(files, expected)

    def test_match_excluded_dir_incorrect_glob(self):
        incorrect_glob = "more_samples"
        expected = ["empty_for_testing.py", "insecure_random.py", "make_request.py"]
        files = match_files("tests/samples/", incorrect_glob)
        self._assert_expected(files, expected)

    def test_match_excluded_dir_correct_glob(self):
        correct_globs = ["**/more_samples/**", "*/more_samples/*"]
        for correct_glob in correct_globs:
            expected = ["insecure_random.py", "make_request.py"]
            files = match_files("tests/samples/", correct_glob)
            self._assert_expected(files, expected)

    def test_match_excluded_multiple(self):
        expected = ["insecure_random.py"]
        files = match_files("tests/samples/", "*request.py,*empty*")
        self._assert_expected(files, expected)

    def test_match_included(self):
        expected = ["empty_for_testing.py", "insecure_random.py", "make_request.py"]
        files = match_files("tests/samples/", include_paths="*request.py")
        self._assert_expected(files, expected)

    def test_match_excluded_precedence_over_included(self):
        expected = ["empty_for_testing.py", "insecure_random.py"]
        files = match_files(
            "tests/samples/", exclude_paths="*request.py", include_paths="*request.py"
        )
        self._assert_expected(files, expected)
