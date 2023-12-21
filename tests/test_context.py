from codemodder.context import CodemodExecutionContext as Context
from codemodder.dependency import Security
from codemodder.registry import load_registered_codemods
from codemodder.project_analysis.python_repo_manager import PythonRepoManager


class TestContext:
    def test_successful_dependency_description(self, mocker):
        registry = load_registered_codemods()
        repo_manager = PythonRepoManager(mocker.Mock())
        codemod = registry.match_codemods(codemod_include=["url-sandbox"])[0]

        context = Context(mocker.Mock(), True, False, registry, repo_manager)
        context.add_dependencies(codemod.id, {Security})

        pkg_store_name = "pyproject.toml"

        pkg_store = mocker.Mock()
        pkg_store.type.value = pkg_store_name
        mocker.patch(
            "codemodder.project_analysis.file_parsers.base_parser.BaseParser.parse",
            return_value=[pkg_store],
        )

        context.process_dependencies(codemod.id)
        description = context.add_description(codemod)

        assert description.startswith(codemod.description)
        assert "## Dependency Updates\n" in description
        assert (
            f"We have automatically added this dependency to your project's `{pkg_store_name}` file."
            in description
        )
        assert Security.description in description
        assert "### Manual Installation\n" not in description

    def test_failed_dependency_description(self, mocker):
        registry = load_registered_codemods()
        repo_manager = PythonRepoManager(mocker.Mock())
        codemod = registry.match_codemods(codemod_include=["url-sandbox"])[0]

        context = Context(mocker.Mock(), True, False, registry, repo_manager)
        context.add_dependencies(codemod.id, {Security})

        mocker.patch(
            "codemodder.project_analysis.python_repo_manager.PythonRepoManager._parse_all_stores",
            return_value=[],
        )

        context.process_dependencies(codemod.id)
        description = context.add_description(codemod)

        assert description.startswith(codemod.description)
        assert "## Dependency Updates\n" in description
        assert Security.description in description
        assert "### Manual Installation\n" in description
        assert (
            f"""For `setup.py`:
```diff
 install_requires=[
+    "{Security.requirement}",
 ],
```"""
            in description
        )
