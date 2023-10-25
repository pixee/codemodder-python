from codemodder.project_analysis.python_repo_manager import PythonRepoManager


class TestPythonRepoManager:
    def test_package_stores(self, pkg_with_reqs_txt):
        rm = PythonRepoManager(pkg_with_reqs_txt)
        stores = rm.package_stores
        assert len(stores) == 1
