import pytest

from codemodder.project_analysis.file_parsers import SetupPyParser


@pytest.fixture(scope="module")
def pkg_with_setup_py(tmp_path_factory):
    base_dir = tmp_path_factory.mktemp("foo")
    setup_py = base_dir / "setup.py"
    data = """\
# -*- coding: utf-8 -*-
# a comment
from sys import platform, version_info

root_dir = path.abspath(path.dirname(__file__))

print(root_dir)

setup(
    name="test pkg",
    description="testing",
    long_description=read("README.md"),
    # The project's main homepage.
    # Author details
    author="Pixee",
    packages=find_packages("src"),
    package_dir={"": "src"},
    python_requires=">3.6",
    install_requires=[
        "protobuf>=3.12,<3.18; python_version < '3'",
        "protobuf>=3.12,<4; python_version >= '3'",
        "psutil>=5.7,<6",
        "requests>=2.4.2,<3",
    ],
    entry_points={},
)
    """
    setup_py.write_text(data)
    return base_dir


class TestSetupPyParser:
    def test_parse(self, pkg_with_setup_py):
        parser = SetupPyParser(pkg_with_setup_py)
        found = parser.parse()
        assert len(found) == 1
        store = found[0]
        assert store.type.value == "setup.py"
        assert store.file == pkg_with_setup_py / parser.file_type.value
        assert store.py_versions == [">3.6"]
        assert len(store.dependencies) == 4

    def test_parse_no_file(self, pkg_with_setup_py):
        parser = SetupPyParser(pkg_with_setup_py / "foo")
        found = parser.parse()
        assert len(found) == 0

    def test_open_error(self, pkg_with_setup_py, mocker):
        mocker.patch("builtins.open", side_effect=Exception)
        parser = SetupPyParser(pkg_with_setup_py)
        found = parser.parse()
        assert len(found) == 0

    def test_parser_error(self, pkg_with_setup_py, mocker):
        mocker.patch(
            "codemodder.project_analysis.file_parsers.setup_py_file_parser.cst.Module.visit",
            side_effect=Exception,
        )
        parser = SetupPyParser(pkg_with_setup_py)
        found = parser.parse()
        assert len(found) == 0
