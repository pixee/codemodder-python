import os

import pytest
from openai import AzureOpenAI, OpenAI

from codemodder.context import CodemodExecutionContext as Context
from codemodder.dependency import Security
from codemodder.llm import DEFAULT_AZURE_OPENAI_API_VERSION, MisconfiguredAIClient
from codemodder.project_analysis.python_repo_manager import PythonRepoManager
from codemodder.registry import load_registered_codemods


@pytest.fixture(autouse=True)
def disable_write_dependencies(mocker):
    """
    Unit tests should not write any dependency files
    """
    mocker.patch(
        "codemodder.dependency_management.dependency_manager.DependencyManager.write",
        # In conftest.py the return value is set to None
        # We need a mocked value for the tests in this file
    )


class TestContext:
    def test_successful_dependency_description(self, mocker):
        registry = load_registered_codemods()
        repo_manager = PythonRepoManager(mocker.Mock())
        codemod = registry.match_codemods(codemod_include=["pixee:python/url-sandbox"])[
            0
        ]

        context = Context(
            mocker.Mock(), True, False, registry, None, repo_manager, [], []
        )
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
        codemod = registry.match_codemods(codemod_include=["pixee:python/url-sandbox"])[
            0
        ]

        context = Context(
            mocker.Mock(), True, False, registry, None, repo_manager, [], []
        )
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

    def test_setup_llm_client_no_env_vars(self, mocker):
        mocker.patch.dict(os.environ, clear=True)
        context = Context(
            mocker.Mock(),
            True,
            False,
            load_registered_codemods(),
            None,
            PythonRepoManager(mocker.Mock()),
            [],
            [],
        )
        assert context.llm_client is None

    def test_setup_openai_llm_client(self, mocker):
        mocker.patch.dict(os.environ, {"CODEMODDER_OPENAI_API_KEY": "test"})
        context = Context(
            mocker.Mock(),
            True,
            False,
            load_registered_codemods(),
            None,
            PythonRepoManager(mocker.Mock()),
            [],
            [],
        )
        assert isinstance(context.llm_client, OpenAI)

    def test_setup_azure_llm_client(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "CODEMODDER_AZURE_OPENAI_API_KEY": "test",
                "CODEMODDER_AZURE_OPENAI_ENDPOINT": "test",
            },
        )
        context = Context(
            mocker.Mock(),
            True,
            False,
            load_registered_codemods(),
            None,
            PythonRepoManager(mocker.Mock()),
            [],
            [],
        )
        assert isinstance(context.llm_client, AzureOpenAI)
        assert context.llm_client._api_version == DEFAULT_AZURE_OPENAI_API_VERSION

    @pytest.mark.parametrize(
        "env_var",
        ["CODEMODDER_AZURE_OPENAI_API_KEY", "CODEMODDER_AZURE_OPENAI_ENDPOINT"],
    )
    def test_setup_azure_llm_client_missing_one(self, mocker, env_var):
        mocker.patch.dict(os.environ, {env_var: "test"})
        with pytest.raises(MisconfiguredAIClient):
            Context(
                mocker.Mock(),
                True,
                False,
                load_registered_codemods(),
                None,
                PythonRepoManager(mocker.Mock()),
                [],
                [],
            )

    def test_get_api_version_from_env(self, mocker):
        version = "fake-version"
        mocker.patch.dict(
            os.environ,
            {
                "CODEMODDER_AZURE_OPENAI_API_KEY": "test",
                "CODEMODDER_AZURE_OPENAI_ENDPOINT": "test",
                "CODEMODDER_AZURE_OPENAI_API_VERSION": version,
            },
        )
        context = Context(
            mocker.Mock(),
            True,
            False,
            load_registered_codemods(),
            None,
            PythonRepoManager(mocker.Mock()),
            [],
            [],
        )
        assert isinstance(context.llm_client, AzureOpenAI)
        assert context.llm_client._api_version == version
