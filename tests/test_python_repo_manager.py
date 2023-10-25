from codemodder.project_analysis.python_repo_manager import PythonRepoManager


class TestPythonRepoManager:
    def test_package_stores(self, dir_with_pkg_managers):
        rm = PythonRepoManager(dir_with_pkg_managers)
        stores = rm.package_stores
        assert len(stores) == 1
