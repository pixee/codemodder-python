import pytest
from textwrap import dedent
from codemodder.dependency_management.setup_py_writer import SetupPyWriter
from codemodder.project_analysis.file_parsers.package_store import (
    PackageStore,
    FileType,
)
from packaging.requirements import Requirement
from codemodder.dependency import DefusedXML, Security

TEST_DEPENDENCIES = [Requirement("defusedxml==0.7.1"), Requirement("security~=1.2.0")]


@pytest.mark.parametrize("dry_run", [True, False])
def test_update_setuppy_dependencies(tmpdir, dry_run):
    original = """
    from setuptools import setup
    setup(
        name="test pkg",
        description="testing",
        long_description="...",
        author="Pixee",
        packages=find_packages("src"),
        package_dir={"": "src"},
        python_requires=">3.6",
        install_requires=[
            "protobuf>=3.12,<3.18; python_version < '3'",
            "protobuf>=3.12,<4; python_version >= '3'",
            "psutil>=5.7,<6",
            "requests>=2.4.2,<3"
        ],
        entry_points={},
    )
    """

    dependency_file = tmpdir.join("setup.py")
    dependency_file.write(dedent(original))

    store = PackageStore(
        type=FileType.SETUP_PY,
        file=str(dependency_file),
        dependencies=set(),
        py_versions=[">=3.6"],
    )

    writer = SetupPyWriter(store, tmpdir)
    dependencies = [DefusedXML, Security]
    changeset = writer.write(dependencies, dry_run=dry_run)

    after = """
        from setuptools import setup
        setup(
            name="test pkg",
            description="testing",
            long_description="...",
            author="Pixee",
            packages=find_packages("src"),
            package_dir={"": "src"},
            python_requires=">3.6",
            install_requires=[
                "protobuf>=3.12,<3.18; python_version < '3'",
                "protobuf>=3.12,<4; python_version >= '3'",
                "psutil>=5.7,<6",
                "requests>=2.4.2,<3", "defusedxml~=0.7.1", "security~=1.2.0"
            ],
            entry_points={},
        )
        """
    assert dependency_file.read() == (dedent(original) if dry_run else dedent(after))

    assert changeset is not None
    assert changeset.path == dependency_file.basename
    res = (
        "--- \n"
        "+++ \n"
        "@@ -12,7 +12,7 @@\n"
        """         "protobuf>=3.12,<3.18; python_version < '3'",\n"""
        """         "protobuf>=3.12,<4; python_version >= '3'",\n"""
        """         "psutil>=5.7,<6",\n"""
        """-        "requests>=2.4.2,<3"\n"""
        """+        "requests>=2.4.2,<3", "defusedxml~=0.7.1", "security~=1.2.0"\n"""
        "     ],\n "
        "    entry_points={},\n"
        " )\n"
    )
    assert changeset.diff == res
    assert len(changeset.changes) == 2
    change_one = changeset.changes[0]

    assert change_one.lineNumber == 14
    assert change_one.description == DefusedXML.build_description()
    assert change_one.properties == {
        "contextual_description": True,
        "contextual_description_position": "right",
    }
    change_two = changeset.changes[1]
    assert change_two.lineNumber == 14
    assert change_two.description == Security.build_description()
    assert change_two.properties == {
        "contextual_description": True,
        "contextual_description_position": "right",
    }


def test_other_setup_func(tmpdir):
    original = """
    from something import setup
    setup(
        name="test pkg",
        install_requires=[
            "protobuf>=3.12,<3.18; python_version < '3'",
            "protobuf>=3.12,<4; python_version >= '3'",
            "psutil>=5.7,<6",
            "requests>=2.4.2,<3"
        ],
        entry_points={},
    )
    """

    dependency_file = tmpdir.join("setup.py")
    dependency_file.write(dedent(original))

    store = PackageStore(
        type=FileType.SETUP_PY,
        file=str(dependency_file),
        dependencies=set(),
        py_versions=[">=3.6"],
    )

    writer = SetupPyWriter(store, tmpdir)
    dependencies = [DefusedXML, Security]
    changeset = writer.write(dependencies)
    assert dependency_file.read() == dedent(original)
    assert changeset is None


def test_not_setup_file(tmpdir):
    original = """
        from setuptools import setup
        setup(
            name="test pkg",
            description="testing",
            long_description="...",
            author="Pixee",
            packages=find_packages("src"),
            package_dir={"": "src"},
            python_requires=">3.6",
            install_requires=[
                "protobuf>=3.12,<3.18; python_version < '3'",
                "protobuf>=3.12,<4; python_version >= '3'",
                "psutil>=5.7,<6",
                "requests>=2.4.2,<3"
            ],
            entry_points={},
        )
        """

    dependency_file = tmpdir.join("not-setup.py")
    dependency_file.write(dedent(original))

    store = PackageStore(
        type=FileType.SETUP_PY,
        file=str(dependency_file),
        dependencies=set(),
        py_versions=[">=3.6"],
    )

    writer = SetupPyWriter(store, tmpdir)
    dependencies = [DefusedXML, Security]
    changeset = writer.write(dependencies)
    assert dependency_file.read() == dedent(original)
    assert changeset is None


def test_setup_call_no_install_requires(tmpdir):
    original = """
    from setuptools import setup
    setup(
        name="test pkg",
        description="testing",
        long_description="...",
        author="Pixee",
        packages=find_packages("src"),
        package_dir={"": "src"},
        python_requires=">3.6",
    )
    """

    dependency_file = tmpdir.join("setup.py")
    dependency_file.write(dedent(original))

    store = PackageStore(
        type=FileType.SETUP_PY,
        file=str(dependency_file),
        dependencies=set(),
        py_versions=[">=3.6"],
    )

    writer = SetupPyWriter(store, tmpdir)
    dependencies = [DefusedXML, Security]
    changeset = writer.write(dependencies)
    assert dependency_file.read() == dedent(original)
    assert changeset is None


def test_setup_no_existing_requirements(tmpdir):
    original = """
    from setuptools import setup
    setup(
        name="test pkg",
        description="testing",
        long_description="...",
        author="Pixee",
        packages=find_packages("src"),
        package_dir={"": "src"},
        python_requires=">3.6",
        install_requires=[],
        entry_points={},
    )
    """
    dependency_file = tmpdir.join("setup.py")
    dependency_file.write(dedent(original))

    store = PackageStore(
        type=FileType.SETUP_PY,
        file=str(dependency_file),
        dependencies=set(),
        py_versions=[">=3.6"],
    )

    writer = SetupPyWriter(store, tmpdir)
    dependencies = [DefusedXML, Security]
    changeset = writer.write(dependencies)

    assert dependency_file.read() == dedent(original)
    assert changeset is None


def test_setup_call_bad_install_requires(tmpdir):
    original = """
    from setuptools import setup
    setup(
        name="test pkg",
        description="testing",
        long_description="...",
        author="Pixee",
        packages=find_packages("src"),
        package_dir={"": "src"},
        python_requires=">3.6",
        install_requires="some-package",
    )
    """
    dependency_file = tmpdir.join("setup.py")
    dependency_file.write(dedent(original))

    store = PackageStore(
        type=FileType.SETUP_PY,
        file=str(dependency_file),
        dependencies=set(),
        py_versions=[">=3.6"],
    )

    writer = SetupPyWriter(store, tmpdir)
    dependencies = [DefusedXML, Security]
    changeset = writer.write(dependencies)

    assert dependency_file.read() == dedent(original)
    assert changeset is None


@pytest.mark.skip("Need to add support.")
def test_setup_call_requirements_separate(tmpdir):
    original = """
    from setuptools import setup
    requirements = [
            "protobuf>=3.12,<3.18; python_version < '3'",
            "protobuf>=3.12,<4; python_version >= '3'",
            "psutil>=5.7,<6",
            "requests>=2.4.2,<3"
    ]
    setup(
        name="test pkg",
        description="testing",
        long_description="...",
        author="Pixee",
        packages=find_packages("src"),
        package_dir={"": "src"},
        python_requires=">3.6",
        install_requires=requirements,
        entry_points={},
    )
    """
    dependency_file = tmpdir.join("setup.py")
    dependency_file.write(dedent(original))

    store = PackageStore(
        type=FileType.SETUP_PY,
        file=str(dependency_file),
        dependencies=set(),
        py_versions=[">=3.6"],
    )

    writer = SetupPyWriter(store, tmpdir)
    dependencies = [DefusedXML, Security]
    changeset = writer.write(dependencies)

    after = """
    from setuptools import setup
    requirements = [
            "protobuf>=3.12,<3.18; python_version < '3'",
            "protobuf>=3.12,<4; python_version >= '3'",
            "psutil>=5.7,<6",
            "requests>=2.4.2,<3", "defusedxml==0.7.1", "security~=1.2.0"
    ]
    setup(
        name="test pkg",
        description="testing",
        long_description="...",
        author="Pixee",
        packages=find_packages("src"),
        package_dir={"": "src"},
        python_requires=">3.6",
        install_requires=requirements,
        entry_points={},
    )
    """
    assert dependency_file.read() == dedent(after)

    assert changeset is not None
    assert changeset.path == dependency_file.basename
    res = (
        "--- \n"
        "+++ \n"
        "@@ -12,7 +12,7 @@\n"
        """         "protobuf>=3.12,<3.18; python_version < '3'",\n"""
        """         "protobuf>=3.12,<4; python_version >= '3'",\n"""
        """         "psutil>=5.7,<6",\n"""
        """-        "requests>=2.4.2,<3"\n"""
        """+        "requests>=2.4.2,<3", "defusedxml~=0.7.1", "security~=1.2.0"\n"""
        "     ],\n "
        "    entry_points={},\n"
        " )\n"
    )
    assert changeset.diff == res
    assert len(changeset.changes) == 2
    change_one = changeset.changes[0]

    assert change_one.lineNumber == 14
    assert change_one.description == DefusedXML.build_description()
    assert change_one.properties == {
        "contextual_description": True,
        "contextual_description_position": "right",
    }
    change_two = changeset.changes[1]
    assert change_two.lineNumber == 14
    assert change_two.description == Security.build_description()
    assert change_two.properties == {
        "contextual_description": True,
        "contextual_description_position": "right",
    }
