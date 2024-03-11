from textwrap import dedent

import mock
import pytest

from codemodder.codetf import DiffSide
from codemodder.dependency import DefusedXML, Security
from codemodder.dependency_management.setupcfg_writer import SetupCfgWriter
from codemodder.project_analysis.file_parsers.package_store import (
    FileType,
    PackageStore,
)


@pytest.mark.parametrize("dry_run", [True, False])
def test_update_dependencies(tmpdir, dry_run):
    orig_setupcfg = """\
        [metadata]
        name = my_package
        version = attr: my_package.VERSION

        # some other stuff

        [options]
        include_package_data = True
        python_requires = >=3.7
        install_requires =
            requests
            importlib-metadata; python_version<"3.8"
    """

    setup_cfg = tmpdir.join("setup.cfg")
    setup_cfg.write(dedent(orig_setupcfg))

    store = PackageStore(
        type=FileType.SETUP_CFG,
        file=setup_cfg,
        dependencies=set(),
        py_versions=[">=3.7"],
    )

    writer = SetupCfgWriter(store, tmpdir)
    dependencies = [DefusedXML, Security]
    changeset = writer.write(dependencies, dry_run=dry_run)

    updated_setupcfg = f"""\
        [metadata]
        name = my_package
        version = attr: my_package.VERSION

        # some other stuff

        [options]
        include_package_data = True
        python_requires = >=3.7
        install_requires =
            requests
            importlib-metadata; python_version<"3.8"
            {DefusedXML.requirement}
            {Security.requirement}
    """

    assert setup_cfg.read() == (
        dedent(orig_setupcfg) if dry_run else dedent(updated_setupcfg)
    )

    assert changeset is not None
    assert changeset.path == setup_cfg.basename
    res = (
        "--- \n"
        "+++ \n"
        "@@ -10,3 +10,5 @@\n"
        """ install_requires =\n"""
        """     requests\n"""
        """     importlib-metadata; python_version<"3.8"\n"""
        f"""+    {DefusedXML.requirement}\n"""
        f"""+    {Security.requirement}\n"""
    )
    assert changeset.diff == res
    assert len(changeset.changes) == 2
    change_one = changeset.changes[0]

    assert change_one.lineNumber == 13
    assert change_one.description == DefusedXML.build_description()
    assert change_one.diffSide == DiffSide.RIGHT
    assert change_one.properties == {
        "contextual_description": True,
        "contextual_description_position": "right",
    }
    change_two = changeset.changes[1]
    assert change_two.lineNumber == 14
    assert change_two.description == Security.build_description()
    assert change_two.diffSide == DiffSide.RIGHT
    assert change_two.properties == {
        "contextual_description": True,
        "contextual_description_position": "right",
    }


def test_add_same_dependency_only_once(tmpdir):
    orig_setupcfg = """\
        [metadata]
        name = my_package
        version = attr: my_package.VERSION

        # some other stuff

        [options]
        include_package_data = True
        python_requires = >=3.7
        install_requires =
            requests
            importlib-metadata; python_version<"3.8"
    """

    setup_cfg = tmpdir.join("setup.cfg")
    setup_cfg.write(dedent(orig_setupcfg))

    store = PackageStore(
        type=FileType.SETUP_CFG,
        file=setup_cfg,
        dependencies=set(),
        py_versions=[">=3.7"],
    )

    writer = SetupCfgWriter(store, tmpdir)
    dependencies = [Security, Security]
    writer.write(dependencies)

    updated_setupcfg = f"""\
        [metadata]
        name = my_package
        version = attr: my_package.VERSION

        # some other stuff

        [options]
        include_package_data = True
        python_requires = >=3.7
        install_requires =
            requests
            importlib-metadata; python_version<"3.8"
            {Security.requirement}
    """

    assert setup_cfg.read() == dedent(updated_setupcfg)


def test_dont_add_existing_dependency(tmpdir):
    orig_setupcfg = """\
        [metadata]
        name = my_package
        version = attr: my_package.VERSION

        # some other stuff

        [options]
        include_package_data = True
        python_requires = >=3.7
        install_requires =
            requests
            security~=1.2.0
            importlib-metadata; python_version<"3.8"
    """

    setup_cfg = tmpdir.join("setup.cfg")
    setup_cfg.write(dedent(orig_setupcfg))

    store = PackageStore(
        type=FileType.SETUP_CFG,
        file=setup_cfg,
        dependencies=set([Security.requirement]),
        py_versions=[">=3.7"],
    )

    writer = SetupCfgWriter(store, tmpdir)
    dependencies = [Security]
    writer.write(dependencies)

    assert setup_cfg.read() == dedent(orig_setupcfg)


def test_no_dependencies(tmpdir):
    orig_setupcfg = """\
        [metadata]
        name = my_package
        version = attr: my_package.VERSION

        # some other stuff

        [options]
        include_package_data = True
        python_requires = >=3.7
        install_requires =
    """
    setup_cfg = tmpdir.join("setup.cfg")
    setup_cfg.write(dedent(orig_setupcfg))

    store = PackageStore(
        type=FileType.SETUP_CFG,
        file=setup_cfg,
        dependencies=set(),
        py_versions=[">=3.7"],
    )

    writer = SetupCfgWriter(store, tmpdir)
    dependencies = [Security]
    writer.write(dependencies)

    assert setup_cfg.read() == dedent(orig_setupcfg)


def test_cfg_bad_formatting(tmpdir):
    orig_setupcfg = """\
        [metadata]
        name = my_package
        version = attr: my_package.VERSION

        # some other stuff

        [options]
        include_package_data = True
        python_requires = >=3.7
        install_requires =
        requests
        importlib-metadata; python_version<"3.8"
    """

    setup_cfg = tmpdir.join("setup.cfg")
    setup_cfg.write(dedent(orig_setupcfg))

    store = PackageStore(
        type=FileType.SETUP_CFG,
        file=setup_cfg,
        dependencies=set(),
        py_versions=[">=3.7"],
    )

    writer = SetupCfgWriter(store, tmpdir)
    dependencies = [Security, Security]
    writer.write(dependencies)
    assert setup_cfg.read() == dedent(orig_setupcfg)


@mock.patch(
    "codemodder.dependency_management.setupcfg_writer.SetupCfgWriter.build_new_lines",
    return_value=None,
)
def test_cfg_cant_build_newlines(_, tmpdir):
    orig_setupcfg = """\
        [metadata]
        name = my_package
        version = attr: my_package.VERSION

        # some other stuff

        [options]
        include_package_data = True
        python_requires = >=3.7
        install_requires =
            requests
            importlib-metadata; python_version<"3.8"
    """

    setup_cfg = tmpdir.join("setup.cfg")
    setup_cfg.write(dedent(orig_setupcfg))

    store = PackageStore(
        type=FileType.SETUP_CFG,
        file=setup_cfg,
        dependencies=set(),
        py_versions=[">=3.7"],
    )

    writer = SetupCfgWriter(store, tmpdir)
    dependencies = [Security, Security]
    writer.write(dependencies)
    assert setup_cfg.read() == dedent(orig_setupcfg)


def test_cfg_inline_dependencies(tmpdir):
    orig_setupcfg = """\
        [metadata]
        name = my_package
        version = attr: my_package.VERSION

        # some other stuff

        [options]
        include_package_data = True
        python_requires = >=3.7
        install_requires = requests, importlib-metadata; python_version<"3.8"
    """

    setup_cfg = tmpdir.join("setup.cfg")
    setup_cfg.write(dedent(orig_setupcfg))

    store = PackageStore(
        type=FileType.SETUP_CFG,
        file=setup_cfg,
        dependencies=set(),
        py_versions=[">=3.7"],
    )

    writer = SetupCfgWriter(store, tmpdir)
    dependencies = [Security, Security]
    changeset = writer.write(dependencies)

    updated_setupcfg = f"""\
        [metadata]
        name = my_package
        version = attr: my_package.VERSION

        # some other stuff

        [options]
        include_package_data = True
        python_requires = >=3.7
        install_requires = requests, importlib-metadata; python_version<"3.8", {Security.requirement},
    """

    assert setup_cfg.read() == dedent(updated_setupcfg)

    res = (
        "--- \n"
        "+++ \n"
        "@@ -7,4 +7,4 @@\n"
        """ [options]\n"""
        """ include_package_data = True\n"""
        """ python_requires = >=3.7\n"""
        """-install_requires = requests, importlib-metadata; python_version<"3.8"\n"""
        f"""+install_requires = requests, importlib-metadata; python_version<"3.8", {Security.requirement},\n"""
    )
    assert changeset.diff == res
    assert len(changeset.changes) == 1
    change_one = changeset.changes[0]

    assert change_one.lineNumber == 10
    assert change_one.description == Security.build_description()
    assert change_one.diffSide == DiffSide.RIGHT
    assert change_one.properties == {
        "contextual_description": True,
        "contextual_description_position": "right",
    }
