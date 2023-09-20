from codemodder.semgrep import run as semgrep_run
from codemodder.registry import CodemodCollection, CodemodRegistry
from core_codemods import SecureRandom, UrlSandbox


class TestSemgrep:
    def _assert_url_sandbox_results(self, results):
        assert len(results) == 1

        result = results[0]

        assert result["ruleId"].endswith("sandbox-url-creation")
        assert result["message"]["text"] == "Unbounded URL creation"

        location = result["locations"][0]["physicalLocation"]
        assert location["artifactLocation"]["uri"] == "tests/samples/make_request.py"

        assert location["region"]["startLine"] == 3
        assert location["region"]["endLine"] == 3
        assert location["region"]["snippet"]["text"] == 'requests.get("www.google.com")'

    def _assert_secure_random_results(self, results):
        assert len(results) == 1
        result = results[0]
        assert result["ruleId"].endswith("secure-random")
        assert result["message"]["text"] == "Semgrep found a match"

        location = result["locations"][0]["physicalLocation"]
        assert location["artifactLocation"]["uri"] == "tests/samples/insecure_random.py"

        assert location["region"]["startLine"] == 3
        assert location["region"]["endLine"] == 3
        assert location["region"]["snippet"]["text"] == "random.random()"

    def test_two_codemods(self, mocker):
        context = mocker.MagicMock(directory="tests/samples")

        collection = CodemodCollection(
            origin="pixee",
            codemods=[SecureRandom, UrlSandbox],
            docs_module="core_codemods.docs",
            semgrep_config_module="core_codemods.semgrep",
        )
        registry = CodemodRegistry()
        registry.add_codemod_collection(collection)
        results_by_path_and_id = semgrep_run(
            context,
            registry.match_codemods(),
        )

        assert sorted(results_by_path_and_id.keys()) == [
            "tests/samples/insecure_random.py",
            "tests/samples/make_request.py",
            "tests/samples/unverified_request.py",
        ]

        url_sandbox_results = results_by_path_and_id["tests/samples/make_request.py"][
            "sandbox-url-creation"
        ]
        self._assert_url_sandbox_results(url_sandbox_results)

        secure_random = results_by_path_and_id["tests/samples/insecure_random.py"][
            "secure-random"
        ]
        self._assert_secure_random_results(secure_random)
