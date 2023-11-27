from textwrap import dedent

from packaging.requirements import Requirement
from codemodder.dependency_management.pyproject_writer import PyprojectWriter


def test_update_pyproject_dependencies(tmpdir):
    orig_pyproject = """\
        [build-system]
        requires = ["setuptools", "setuptools_scm>=8"]
        build-backend = "setuptools.build_meta"

        [project]
        dynamic = ["version"]
        name = "codemodder"
        requires-python = ">=3.10.0"
        readme = "README.md"
        dependencies = [
            "libcst~=1.1.0",
            "pylint~=3.0.0",
            "PyYAML~=6.0.0",
        ]
    """

    pyproject_toml = tmpdir.join("pyproject.toml")
    pyproject_toml.write(dedent(orig_pyproject))

    writer = PyprojectWriter(pyproject_toml)
    writer.write([Requirement("defusedxml~=0.7.1"), Requirement("security~=1.2.0")])

    updated_pyproject = """\
        [build-system]
        requires = ["setuptools", "setuptools_scm>=8"]
        build-backend = "setuptools.build_meta"

        [project]
        dynamic = ["version"]
        name = "codemodder"
        requires-python = ">=3.10.0"
        readme = "README.md"
        dependencies = [
            "libcst~=1.1.0",
            "pylint~=3.0.0",
            "PyYAML~=6.0.0",
            "defusedxml~=0.7.1",
            "security~=1.2.0",
        ]
    """

    assert pyproject_toml.read() == dedent(updated_pyproject)
