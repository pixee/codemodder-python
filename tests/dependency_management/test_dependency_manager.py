import pytest

from codemodder.codetf import ChangeSet
from codemodder.dependency import DefusedXML, Security
from codemodder.dependency_management import DependencyManager
from codemodder.project_analysis.file_parsers import (
    RequirementsTxtParser,
    SetupCfgParser,
)
from codemodder.project_analysis.file_parsers.package_store import PackageStore


@pytest.fixture(autouse=True, scope="module")
def disable_write_dependencies():
    """Override fixture from conftest.py in order to allow testing"""


class TestDependencyManager:
    def test_cant_write_unknown_store(self, tmpdir):
        store = PackageStore(
            type="unknown", file="idk.txt", dependencies=set(), py_versions=[]
        )

        dm = DependencyManager(store, tmpdir)
        dependencies = [DefusedXML, Security]

        changeset = dm.write(dependencies)
        assert changeset is None

    def test_write_for_requirements_txt(self, pkg_with_reqs_txt):
        parser = RequirementsTxtParser(pkg_with_reqs_txt)
        stores = parser.parse()
        assert len(stores) == 1
        dm = DependencyManager(stores[0], pkg_with_reqs_txt)
        dependencies = [DefusedXML, Security]

        changeset = dm.write(dependencies)
        assert isinstance(changeset, ChangeSet)
        assert len(changeset.changes)

    def test_write_for_setup_cfg(self, pkg_with_setup_cfg):
        parser = SetupCfgParser(pkg_with_setup_cfg)
        stores = parser.parse()
        assert len(stores) == 1
        dm = DependencyManager(stores[0], pkg_with_setup_cfg)
        dependencies = [DefusedXML, Security]

        changeset = dm.write(dependencies)
        assert isinstance(changeset, ChangeSet)
        assert len(changeset.changes)
