import os

import pytest
from azure.ai.inference import ChatCompletionsClient
from openai import AzureOpenAI, OpenAI

from codemodder.codetf import (
    DetectionTool,
    DiffSide,
    Finding,
    Rule,
    UnfixedFinding,
)
from codemodder.codetf.common import FixQuality, Rating
from codemodder.codetf.v2.codetf import (
    AIMetadata,
)
from codemodder.codetf.v2.codetf import Change as V2Change
from codemodder.codetf.v2.codetf import ChangeSet as V2ChangeSet
from codemodder.codetf.v2.codetf import (
    Strategy,
)
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

    def test_setup_llm_clients_no_env_vars(self, mocker):
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
        assert context.openai_llm_client is None
        assert context.azure_llama_llm_client is None

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
        assert isinstance(context.openai_llm_client, OpenAI)

    def test_setup_both_llm_clients(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "CODEMODDER_OPENAI_API_KEY": "test",
                "CODEMODDER_AZURE_LLAMA_API_KEY": "test",
                "CODEMODDER_AZURE_LLAMA_ENDPOINT": "test",
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
        assert isinstance(context.openai_llm_client, OpenAI)
        assert isinstance(context.azure_llama_llm_client, ChatCompletionsClient)

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
        assert isinstance(context.openai_llm_client, AzureOpenAI)
        assert (
            context.openai_llm_client._api_version == DEFAULT_AZURE_OPENAI_API_VERSION
        )

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

    def test_setup_azure_llama_llm_client(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "CODEMODDER_AZURE_LLAMA_API_KEY": "test",
                "CODEMODDER_AZURE_LLAMA_ENDPOINT": "test",
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
        assert isinstance(context.azure_llama_llm_client, ChatCompletionsClient)

    @pytest.mark.parametrize(
        "env_var",
        ["CODEMODDER_AZURE_LLAMA_API_KEY", "CODEMODDER_AZURE_LLAMA_ENDPOINT"],
    )
    def test_setup_azure_llama_llm_client_missing_one(self, mocker, env_var):
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
        assert isinstance(context.openai_llm_client, AzureOpenAI)
        assert context.openai_llm_client._api_version == version

    def test_disable_ai_client_openai(self, mocker):
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
            ai_client=False,
        )
        assert context.openai_llm_client is None

    def test_disable_ai_client_azure(self, mocker):
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
            ai_client=False,
        )
        assert context.openai_llm_client is None

    @pytest.mark.parametrize(
        "env_var",
        ["CODEMODDER_AZURE_OPENAI_API_KEY", "CODEMODDER_AZURE_OPENAI_ENDPOINT"],
    )
    def test_no_misconfiguration_ai_client_disabled(self, mocker, env_var):
        mocker.patch.dict(os.environ, {env_var: "test"})
        context = Context(
            mocker.Mock(),
            True,
            False,
            load_registered_codemods(),
            None,
            PythonRepoManager(mocker.Mock()),
            [],
            [],
            ai_client=False,
        )
        assert context.openai_llm_client is None

    def test_compile_results(self, mocker):
        rule = rule = Rule(
            id="roslyn.sonaranalyzer.security.cs:S5131",
            name="Change this code to not reflect user-controlled data.",
            url="https://rules.sonarsource.com/dotnet/RSPEC-5131/",
        )
        mock_codemod_xss = mocker.Mock()
        mock_codemod_xss.id = "sonar:dotnet/xss"
        mock_codemod_xss.summary = "XSS Codemod Summary"
        mock_codemod_xss.description = "XSS Codemod Description"
        mock_codemod_xss.detection_tool = DetectionTool(name="sonar")
        mock_codemod_xss.references = []
        mock_codemod_xss.detection_tool_rules = {rule}

        codemods_to_run = [mock_codemod_xss]

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

        fix_quality = FixQuality(
            safetyRating=Rating(
                score=100,
                description="The changes ...",
            ),
            effectivenessRating=Rating(
                score=100,
                description="The changes ...",
            ),
            cleanlinessRating=Rating(
                score=100,
                description="The changes ...",
            ),
        )
        changeset_data = {
            "sonar:dotnet/xss": [
                V2ChangeSet(
                    path="WebGoat/WebGoatCoins/Autocomplete.ashx.cs",
                    diff="diff",
                    changes=[
                        V2Change(
                            lineNumber=1,
                            description="Added import for System.Net namespace to use WebUtility for HTML encoding.",
                            diffSide=DiffSide.RIGHT,
                            properties=None,
                            packageActions=None,
                            fixedFindings=[
                                Finding(
                                    id="AY-cCz4neXIgSHLjbCnv",
                                    rule=rule,
                                )
                            ],
                        ),
                        V2Change(
                            lineNumber=28,
                            description="Wrapped Encoder.ToJSONSAutocompleteString with WebUtility.HtmlEncode to safely encode user input for output.",
                            diffSide=DiffSide.RIGHT,
                            properties=None,
                            packageActions=None,
                            fixedFindings=[
                                Finding(
                                    id="AY-cCz4neXIgSHLjbCnv",
                                    rule=rule,
                                )
                            ],
                        ),
                    ],
                    ai=AIMetadata(
                        provider="openai",
                        model="gpt-4o",
                        tokens=86618,
                        completion_tokens=12110,
                        prompt_tokens=74508,
                    ),
                    strategy=Strategy.ai,
                    provisional=False,
                    fixedFindings=[
                        Finding(
                            id="AY-cCz4neXIgSHLjbCnv",
                            rule=rule,
                        )
                    ],
                    fixQuality=fix_quality,
                )
            ]
        }
        context._changesets_by_codemod = changeset_data

        context._unfixed_findings_by_codemod = {
            mock_codemod_xss.id: [
                UnfixedFinding(
                    rule=rule, path="some/path.cs", lineNumber=10, reason="unfixed"
                )
            ]
        }
        context._failures_by_codemod = {mock_codemod_xss.id: ["failed/file.cs"]}

        results = context.compile_results(codemods_to_run)

        assert len(results) == 1
        assert results[0].changeset[0].fixQuality == fix_quality
        assert results[0].changeset[0].fixedFindings == [
            Finding(
                id="AY-cCz4neXIgSHLjbCnv",
                rule=rule,
            )
        ]
