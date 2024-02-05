from textwrap import dedent
import pytest

from codemodder.change import DiffSide
from codemodder.dependency_management.pyproject_writer import PyprojectWriter
from codemodder.dependency import DefusedXML, Security
from codemodder.project_analysis.file_parsers.package_store import (
    PackageStore,
    FileType,
)


@pytest.mark.parametrize("dry_run", [True, False])
def test_update_pyproject_dependencies(tmpdir, dry_run):
    orig_pyproject = """\
        [build-system]
        requires = ["setuptools", "setuptools_scm>=8"]
        build-backend = "setuptools.build_meta"

        # some comment

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

    store = PackageStore(
        type=FileType.REQ_TXT,
        file=pyproject_toml,
        dependencies=set(),
        py_versions=[">=3.10.0"],
    )

    writer = PyprojectWriter(store, tmpdir)
    dependencies = [DefusedXML, Security]
    changeset = writer.write(dependencies, dry_run=dry_run)

    updated_pyproject = """\
        [build-system]
        requires = ["setuptools", "setuptools_scm>=8"]
        build-backend = "setuptools.build_meta"

        # some comment

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

    assert pyproject_toml.read() == (
        dedent(orig_pyproject) if dry_run else dedent(updated_pyproject)
    )

    assert changeset is not None
    assert changeset.path == pyproject_toml.basename
    res = (
        "--- \n"
        "+++ \n"
        "@@ -13,5 +13,7 @@\n"
        """     "libcst~=1.1.0",\n"""
        """     "pylint~=3.0.0",\n"""
        """     "PyYAML~=6.0.0",\n"""
        """+    "defusedxml~=0.7.1",\n"""
        """+    "security~=1.2.0",\n"""
        " ]\n "
    )
    assert changeset.diff == res
    assert len(changeset.changes) == 2
    change_one = changeset.changes[0]

    assert change_one.lineNumber == 16
    assert change_one.description == DefusedXML.build_description()
    assert change_one.diffSide == DiffSide.RIGHT
    assert change_one.properties == {
        "contextual_description": True,
        "contextual_description_position": "right",
    }
    change_two = changeset.changes[1]
    assert change_two.lineNumber == 17
    assert change_two.description == Security.build_description()
    assert change_two.diffSide == DiffSide.RIGHT
    assert change_two.properties == {
        "contextual_description": True,
        "contextual_description_position": "right",
    }


def test_add_same_dependency_only_once(tmpdir):
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

    store = PackageStore(
        type=FileType.REQ_TXT,
        file=pyproject_toml,
        dependencies=set(),
        py_versions=[">=3.10.0"],
    )

    writer = PyprojectWriter(store, tmpdir)
    dependencies = [Security, Security]
    writer.write(dependencies)

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
            "security~=1.2.0",
        ]
    """

    assert pyproject_toml.read() == dedent(updated_pyproject)


def test_dont_add_existing_dependency(tmpdir):
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
            "security~=1.2.0",
        ]
    """

    pyproject_toml = tmpdir.join("pyproject.toml")
    pyproject_toml.write(dedent(orig_pyproject))

    store = PackageStore(
        type=FileType.REQ_TXT,
        file=pyproject_toml,
        dependencies=set([Security.requirement]),
        py_versions=[">=3.10.0"],
    )

    writer = PyprojectWriter(store, tmpdir)
    dependencies = [Security]
    writer.write(dependencies)

    assert pyproject_toml.read() == dedent(orig_pyproject)


def test_pyproject_no_dependencies(tmpdir):
    orig_pyproject = """\
        [build-system]
        requires = ["setuptools", "setuptools_scm>=8"]
        build-backend = "setuptools.build_meta"
        [project]
        name = "codemodder"
    """

    pyproject_toml = tmpdir.join("pyproject.toml")
    pyproject_toml.write(dedent(orig_pyproject))

    store = PackageStore(
        type=FileType.REQ_TXT,
        file=pyproject_toml,
        dependencies=set(),
        py_versions=[">=3.10.0"],
    )

    writer = PyprojectWriter(store, tmpdir)
    dependencies = [Security]

    writer.write(dependencies)

    assert pyproject_toml.read() == dedent(orig_pyproject)
