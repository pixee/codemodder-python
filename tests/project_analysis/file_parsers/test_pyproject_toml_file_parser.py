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


@pytest.fixture(scope="module")
def pkg_with_pyproject_toml_no_python(tmp_path_factory):
    base_dir = tmp_path_factory.mktemp("foo")
    toml_file = base_dir / "pyproject.toml"
    toml = """\
    [project]
    name = "js_example"
    version = "1.1.0"
    description = "Demonstrates making AJAX requests to Flask."
    readme = "README.rst"
    license = {file = "LICENSE.rst"}
    maintainers = [{name = "Pallets", email = "contact@palletsprojects.com"}]
    dependencies = ["flask"]
    """
    toml_file.write_text(toml)
    return base_dir


@pytest.fixture(scope="module")
def pkg_with_poetry_pyproject(tmp_path_factory):
    base_dir = tmp_path_factory.mktemp("foo")
    toml_file = base_dir / "pyproject.toml"
    toml = """\
    [tool.poetry]
    name = "example-project"
    version = "0.1.0"
    description = "An example project to demonstrate Poetry configuration."
    authors = ["Your Name <your.email@example.com>"]
    
    [build-system]
    requires = ["poetry-core>=1.0.0"]
    build-backend = "poetry.core.masonry.api"
    
    [tool.poetry.dependencies]
    python = "~=3.11.0"
    requests = ">=2.25.1,<3.0.0"
    pandas = "1.2.3"
    libcst = ">1.0"
    """
    toml_file.write_text(toml)
    return base_dir


@pytest.fixture(scope="module")
def pkg_with_poetry_no_deps(tmp_path_factory):
    base_dir = tmp_path_factory.mktemp("foo")
    toml_file = base_dir / "pyproject.toml"
    toml = """\
    [tool.poetry]
    name = "example-project"
    version = "0.1.0"
    description = "An example project to demonstrate Poetry configuration."
    authors = ["Your Name <your.email@example.com>"]

    [build-system]
    requires = ["poetry-core>=1.0.0"]
    build-backend = "poetry.core.masonry.api"
    """
    toml_file.write_text(toml)
    return base_dir


@pytest.fixture(scope="module")
def pkg_with_poetry_multiple_dep_locations(tmp_path_factory):
    base_dir = tmp_path_factory.mktemp("foo")
    toml_file = base_dir / "pyproject.toml"
    toml = """\
    [project]
    name = "example-project"
    version = "0.1.0"
    description = "An example project to demonstrate Poetry configuration."
    authors = ["Your Name <your.email@example.com>"]
    dependencies = [
            "isort~=5.12.0"
           ]

    [build-system]
    requires = ["poetry-core>=1.0.0"]
    build-backend = "poetry.core.masonry.api"

    [tool.poetry.dependencies]
    python = "^3.11"
    requests = "^2.25.1"
    pandas = "^1.2.3"
    libcst = ">1.0"
    """
    toml_file.write_text(toml)
    return base_dir


class TestPyprojectTomlParser:
    def test_parse(self, pkg_with_pyproject_toml):
        parser = PyprojectTomlParser(pkg_with_pyproject_toml)
        found = parser.parse()
        assert len(found) == 1
        store = found[0]
        assert store.type.value == "pyproject.toml"
        assert store.file == pkg_with_pyproject_toml / parser.file_type.value
        assert store.py_versions == [">=3.10.0"]
        assert len(store.dependencies) == 6

    def test_parse_no_python(self, pkg_with_pyproject_toml_no_python):
        parser = PyprojectTomlParser(pkg_with_pyproject_toml_no_python)
        found = parser.parse()
        assert len(found) == 1
        store = found[0]
        assert store.type.value == "pyproject.toml"
        assert store.file == pkg_with_pyproject_toml_no_python / parser.file_type.value
        assert store.py_versions == []
        assert len(store.dependencies) == 1

    def test_parse_no_file(self, pkg_with_pyproject_toml):
        parser = PyprojectTomlParser(pkg_with_pyproject_toml / "foo")
        found = parser.parse()
        assert len(found) == 0

    def test_parser_error(self, pkg_with_pyproject_toml, mocker):
        mocker.patch(
            "codemodder.project_analysis.file_parsers.pyproject_toml_file_parser.toml.load",
            side_effect=Exception,
        )
        parser = PyprojectTomlParser(pkg_with_pyproject_toml)
        found = parser.parse()
        assert len(found) == 0

    def test_parse_poetry(self, pkg_with_poetry_pyproject):
        parser = PyprojectTomlParser(pkg_with_poetry_pyproject)
        found = parser.parse()
        assert len(found) == 1
        store = found[0]
        assert store.type.value == "pyproject.toml"
        assert store.file == pkg_with_poetry_pyproject / parser.file_type.value
        assert store.py_versions == ["~=3.11.0"]
        assert len(store.dependencies) == 3

    def test_parse_poetry_no_deps(self, pkg_with_poetry_no_deps):
        parser = PyprojectTomlParser(pkg_with_poetry_no_deps)
        found = parser.parse()
        assert len(found) == 1
        store = found[0]
        assert store.type.value == "pyproject.toml"
        assert store.file == pkg_with_poetry_no_deps / parser.file_type.value
        assert store.py_versions == []
        assert len(store.dependencies) == 0

    def test_parse_poetry_and_project_dependencies(
        self, pkg_with_poetry_multiple_dep_locations
    ):
        parser = PyprojectTomlParser(pkg_with_poetry_multiple_dep_locations)
        found = parser.parse()
        assert len(found) == 1
        store = found[0]
        assert store.type.value == "pyproject.toml"
        assert (
            store.file
            == pkg_with_poetry_multiple_dep_locations / parser.file_type.value
        )
        assert store.py_versions == ["^3.11"]
        assert len(store.dependencies) == 4
