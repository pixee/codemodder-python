from textwrap import dedent

import pytest

from codemodder.codetf import DiffSide
from codemodder.dependency import DefusedXML, Security
from codemodder.dependency_management.pyproject_writer import (
    TYPE_CHECKER_LIBRARIES,
    PyprojectWriter,
)
from codemodder.project_analysis.file_parsers.package_store import (
    FileType,
    PackageStore,
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
        type=FileType.TOML,
        file=pyproject_toml,
        dependencies=set(),
        py_versions=[">=3.10.0"],
    )

    writer = PyprojectWriter(store, tmpdir)
    dependencies = [DefusedXML, Security]
    changeset = writer.write(dependencies, dry_run=dry_run)

    updated_pyproject = f"""\
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
            "{DefusedXML.requirement}",
            "{Security.requirement}",
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
        f"""+    "{DefusedXML.requirement}",\n"""
        f"""+    "{Security.requirement}",\n"""
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
        type=FileType.TOML,
        file=pyproject_toml,
        dependencies=set(),
        py_versions=[">=3.10.0"],
    )

    writer = PyprojectWriter(store, tmpdir)
    dependencies = [Security, Security]
    writer.write(dependencies)

    updated_pyproject = f"""\
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
            "{Security.requirement}",
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
        type=FileType.TOML,
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
        type=FileType.TOML,
        file=pyproject_toml,
        dependencies=set(),
        py_versions=[">=3.10.0"],
    )

    writer = PyprojectWriter(store, tmpdir)
    dependencies = [Security]

    writer.write(dependencies)

    assert pyproject_toml.read() == dedent(orig_pyproject)


def test_pyproject_poetry(tmpdir):
    orig_pyproject = """\
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
        pandas = "^1.2.3"
        libcst = ">1.0"
    """

    pyproject_toml = tmpdir.join("pyproject.toml")
    pyproject_toml.write(dedent(orig_pyproject))

    store = PackageStore(
        type=FileType.TOML,
        file=pyproject_toml,
        dependencies=set(),
        py_versions=["~=3.11.0"],
    )

    writer = PyprojectWriter(store, tmpdir)
    dependencies = [Security, DefusedXML]
    writer.write(dependencies)

    updated_pyproject = f"""\
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
        pandas = "^1.2.3"
        libcst = ">1.0"
        {Security.requirement.name} = "{ str(Security.requirement.specifier)}"
        {DefusedXML.requirement.name} = "{ str(DefusedXML.requirement.specifier)}"
    """

    assert pyproject_toml.read() == dedent(updated_pyproject)


def test_pyproject_poetry_existing_dependency(tmpdir):
    orig_pyproject = """\
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
        pandas = "^1.2.3"
        libcst = ">1.0"
        defusedxml = "^0.7"
    """

    pyproject_toml = tmpdir.join("pyproject.toml")
    pyproject_toml.write(dedent(orig_pyproject))

    store = PackageStore(
        type=FileType.TOML,
        file=pyproject_toml,
        dependencies=set([DefusedXML.requirement]),
        py_versions=["~=3.11.0"],
    )

    writer = PyprojectWriter(store, tmpdir)
    dependencies = [DefusedXML]
    writer.write(dependencies)

    assert pyproject_toml.read() == dedent(orig_pyproject)


def test_pyproject_poetry_no_deps_section(tmpdir):
    orig_pyproject = """\
        [tool.poetry]
        name = "example-project"
        version = "0.1.0"
        description = "An example project to demonstrate Poetry configuration."
        authors = ["Your Name <your.email@example.com>"]

        [build-system]
        requires = ["poetry-core>=1.0.0"]
        build-backend = "poetry.core.masonry.api"
    """

    pyproject_toml = tmpdir.join("pyproject.toml")
    pyproject_toml.write(dedent(orig_pyproject))

    store = PackageStore(
        type=FileType.TOML,
        file=pyproject_toml,
        dependencies=set(),
        py_versions=[],
    )

    writer = PyprojectWriter(store, tmpdir)
    dependencies = [Security, DefusedXML]
    writer.write(dependencies)

    updated_pyproject = f"""\
        [tool.poetry]
        name = "example-project"
        version = "0.1.0"
        description = "An example project to demonstrate Poetry configuration."
        authors = ["Your Name <your.email@example.com>"]

        [tool.poetry.dependencies]
        {Security.requirement.name} = "{str(Security.requirement.specifier)}"
        {DefusedXML.requirement.name} = "{str(DefusedXML.requirement.specifier)}"

        [build-system]
        requires = ["poetry-core>=1.0.0"]
        build-backend = "poetry.core.masonry.api"
    """

    assert pyproject_toml.read() == dedent(updated_pyproject)


def test_pyproject_poetry_no_declared_deps(tmpdir):
    orig_pyproject = """\
        [tool.poetry]
        name = "example-project"
        version = "0.1.0"
        description = "An example project to demonstrate Poetry configuration."
        authors = ["Your Name <your.email@example.com>"]

        [build-system]
        requires = ["poetry-core>=1.0.0"]
        build-backend = "poetry.core.masonry.api"

        [tool.poetry.dependencies]
        python = "^3.11"
    """

    pyproject_toml = tmpdir.join("pyproject.toml")
    pyproject_toml.write(dedent(orig_pyproject))

    store = PackageStore(
        type=FileType.TOML,
        file=pyproject_toml,
        dependencies=set(),
        py_versions=["~=3.11.0"],
    )

    writer = PyprojectWriter(store, tmpdir)
    dependencies = [Security, DefusedXML]
    writer.write(dependencies)

    updated_pyproject = f"""\
        [tool.poetry]
        name = "example-project"
        version = "0.1.0"
        description = "An example project to demonstrate Poetry configuration."
        authors = ["Your Name <your.email@example.com>"]

        [build-system]
        requires = ["poetry-core>=1.0.0"]
        build-backend = "poetry.core.masonry.api"

        [tool.poetry.dependencies]
        python = "^3.11"
        {Security.requirement.name} = "{str(Security.requirement.specifier)}"
        {DefusedXML.requirement.name} = "{str(DefusedXML.requirement.specifier)}"
    """

    assert pyproject_toml.read() == dedent(updated_pyproject)


@pytest.mark.parametrize("type_checker", TYPE_CHECKER_LIBRARIES)
def test_pyproject_poetry_with_type_checker_tool(tmpdir, type_checker):
    orig_pyproject = f"""\
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
        pandas = "^1.2.3"
        libcst = ">1.0"
        {type_checker} = "==1.0"
    """

    pyproject_toml = tmpdir.join("pyproject.toml")
    pyproject_toml.write(dedent(orig_pyproject))

    store = PackageStore(
        type=FileType.TOML,
        file=pyproject_toml,
        dependencies=set(),
        py_versions=["~=3.11.0"],
    )

    writer = PyprojectWriter(store, tmpdir)
    dependencies = [Security, DefusedXML]
    writer.write(dependencies)

    defusedxml_type_stub = DefusedXML.type_stubs[0]
    updated_pyproject = f"""\
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
        pandas = "^1.2.3"
        libcst = ">1.0"
        {type_checker} = "==1.0"
        {Security.requirement.name} = "{str(Security.requirement.specifier)}"
        {DefusedXML.requirement.name} = "{str(DefusedXML.requirement.specifier)}"
        {defusedxml_type_stub.requirement.name} = "{str(defusedxml_type_stub.requirement.specifier)}"
    """

    assert pyproject_toml.read() == dedent(updated_pyproject)


@pytest.mark.parametrize(
    "dependency_section",
    [
        "[tool.poetry.test.dependencies]",
        "[tool.poetry.dev-dependencies]",
        "[tool.poetry.dev.dependencies]",
        "[tool.poetry.group.test.dependencies]",
    ],
)
@pytest.mark.parametrize("type_checker", TYPE_CHECKER_LIBRARIES)
def test_pyproject_poetry_with_type_checker_tool_without_poetry_deps_section(
    tmpdir, type_checker, dependency_section
):
    orig_pyproject = f"""\
        [tool.poetry]
        name = "example-project"
        version = "0.1.0"
        description = "An example project to demonstrate Poetry configuration."
        authors = ["Your Name <your.email@example.com>"]

        [build-system]
        requires = ["poetry-core>=1.0.0"]
        build-backend = "poetry.core.masonry.api"
        
        {dependency_section}
        {type_checker} = "==1.0"
    """

    pyproject_toml = tmpdir.join("pyproject.toml")
    pyproject_toml.write(dedent(orig_pyproject))

    store = PackageStore(
        type=FileType.TOML,
        file=pyproject_toml,
        dependencies=set(),
        py_versions=["~=3.11.0"],
    )

    writer = PyprojectWriter(store, tmpdir)
    dependencies = [Security, DefusedXML]
    writer.write(dependencies)

    defusedxml_type_stub = DefusedXML.type_stubs[0]
    updated_pyproject = f"""\
        [tool.poetry]
        name = "example-project"
        version = "0.1.0"
        description = "An example project to demonstrate Poetry configuration."
        authors = ["Your Name <your.email@example.com>"]

        [tool.poetry.dependencies]
        {Security.requirement.name} = "{str(Security.requirement.specifier)}"
        {DefusedXML.requirement.name} = "{str(DefusedXML.requirement.specifier)}"

        [build-system]
        requires = ["poetry-core>=1.0.0"]
        build-backend = "poetry.core.masonry.api"
        
        {dependency_section}
        {type_checker} = "==1.0"
        {defusedxml_type_stub.requirement.name} = "{str(defusedxml_type_stub.requirement.specifier)}"
    """

    assert pyproject_toml.read() == dedent(updated_pyproject)


@pytest.mark.parametrize("type_checker", TYPE_CHECKER_LIBRARIES)
def test_pyproject_poetry_with_type_checker_tool_multiple(tmpdir, type_checker):
    orig_pyproject = f"""\
        [build-system]
        requires = ["poetry-core>=1.0.0"]
        build-backend = "poetry.core.masonry.api"
        
        [tool.poetry]
        name = "example-project"
        version = "0.1.0"
        description = "An example project to demonstrate Poetry configuration."
        authors = ["Your Name <your.email@example.com>"]

        [tool.poetry.dependencies]
        python = "~=3.11.0"
        requests = ">=2.25.1,<3.0.0"
        pandas = "^1.2.3"
        libcst = ">1.0"
        
        [tool.poetry.group.test.dependencies]
        {type_checker} = "==1.0"
    """

    pyproject_toml = tmpdir.join("pyproject.toml")
    pyproject_toml.write(dedent(orig_pyproject))

    store = PackageStore(
        type=FileType.TOML,
        file=pyproject_toml,
        dependencies=set(),
        py_versions=["~=3.11.0"],
    )

    writer = PyprojectWriter(store, tmpdir)
    dependencies = [Security, DefusedXML]
    writer.write(dependencies)

    defusedxml_type_stub = DefusedXML.type_stubs[0]
    updated_pyproject = f"""\
        [build-system]
        requires = ["poetry-core>=1.0.0"]
        build-backend = "poetry.core.masonry.api"
        
        [tool.poetry]
        name = "example-project"
        version = "0.1.0"
        description = "An example project to demonstrate Poetry configuration."
        authors = ["Your Name <your.email@example.com>"]

        [tool.poetry.dependencies]
        python = "~=3.11.0"
        requests = ">=2.25.1,<3.0.0"
        pandas = "^1.2.3"
        libcst = ">1.0"
        {Security.requirement.name} = "{str(Security.requirement.specifier)}"
        {DefusedXML.requirement.name} = "{str(DefusedXML.requirement.specifier)}"

        [tool.poetry.group.test.dependencies]
        {type_checker} = "==1.0"
        {defusedxml_type_stub.requirement.name} = "{str(defusedxml_type_stub.requirement.specifier)}"
    """

    assert pyproject_toml.read() == dedent(updated_pyproject)
