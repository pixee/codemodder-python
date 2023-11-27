import pytest

from codemodder.change import ChangeSet
from codemodder.dependency import DefusedXML, Security
from codemodder.dependency_management import DependencyManager
from codemodder.project_analysis.file_parsers import RequirementsTxtParser
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
