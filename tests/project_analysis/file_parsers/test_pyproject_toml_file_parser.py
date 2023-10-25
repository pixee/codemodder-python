# pylint: disable=redefined-outer-name
import pytest
from codemodder.project_analysis.file_parsers import PyprojectTomlParser


@pytest.fixture(scope="module")
def pkg_with_pyproject_toml(tmp_path_factory):
    base_dir = tmp_path_factory.mktemp("foo")
    toml_file = base_dir / "pyproject.toml"
    toml = """\
    [build-system]
    requires = ["setuptools"]
    build-backend = "setuptools.build_meta"

    [project]
    name = "pkg for testing"
    version = "0.60.0"
    requires-python = ">=3.10.0"
    readme = "README.md"
    license = {file = "LICENSE"}
    dependencies = [
        "isort~=5.12.0",
        "libcst~=1.1.0",
        "PyYAML~=6.0.0",
        "semgrep<2",
        "toml~=0.10.2",
        "wrapt~=1.15.0",
    ]
    """
    toml_file.write_text(toml)
    return base_dir


class TestPyprojectTomlParser:
    def test_parse(self, pkg_with_pyproject_toml):
        parser = PyprojectTomlParser(pkg_with_pyproject_toml)
        found = parser.parse()
        assert len(found) == 1
        store = found[0]
        assert store.type == "pyproject.toml"
        assert store.file == str(pkg_with_pyproject_toml / parser.file_name)
        assert store.py_versions == [">=3.10.0"]
        assert len(store.dependencies) == 6

    def test_parse_no_file(self, pkg_with_pyproject_toml):
        parser = PyprojectTomlParser(pkg_with_pyproject_toml / "foo")
        found = parser.parse()
        assert len(found) == 0
