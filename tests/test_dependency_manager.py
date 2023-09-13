import mock
from pathlib import Path
from codemodder.__main__ import run
from codemodder.cli import parse_args
from codemodder.semgrep import run as semgrep_run
from codemodder.dependency_manager import write_dependencies


class TestDependencyManager:
    TEST_DIR = "tests/"

    def test_init_once(self, mocker):
        context = mocker.Mock(directory=self.TEST_DIR, dependencies=[])
        dm = write_dependencies(context)
        expected_path = Path(self.TEST_DIR)
        assert dm.parent_directory == expected_path
        assert dm.dependency_file == expected_path / "samples" / "requirements.txt"
        assert len(dm.dependencies) == 4

        dep = next(iter(dm.dependencies))
        assert str(dep) == "requests==2.31.0"

    @mock.patch("codemodder.dependency_manager.DependencyManagerAbstract._write")
    @mock.patch("codemodder.__main__.semgrep_run", side_effect=semgrep_run)
    def test_dont_write(self, _, write_mock):
        # Tests that dependency manager does not write to file if only
        # codemods that don't change dependencies run.
        args = [
            "tests/samples/",
            "--output",
            "here.txt",
            "--codemod-include=secure-random",
        ]
        res = run(parse_args(args), args)
        assert res == 0
        write_mock.assert_not_called()

    @mock.patch("codemodder.dependency_manager.DependencyManagerAbstract._write")
    @mock.patch("codemodder.__main__.semgrep_run", side_effect=semgrep_run)
    def test_write_expected(self, _, write_mock):
        args = [
            "tests/samples/",
            "--output",
            "here.txt",
            "--codemod-include=url-sandbox",
        ]
        res = run(parse_args(args), args)
        assert res == 0
        write_mock.assert_called()
