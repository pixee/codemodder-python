from codemodder.semgrep import run as semgrep_run


class TestSemgrep:
    def _assert_url_sandbox_results(self, results):
        assert len(results) == 2

        result1 = results[0]
        assert result1["ruleId"] == "codemodder.codemods.semgrep.sandbox-url-creation"
        assert result1["message"]["text"] == "Unbounded URL creation"

        location = result1["locations"][0]["physicalLocation"]
        assert location["artifactLocation"]["uri"] == "tests/samples/make_request.py"

        assert location["region"]["startLine"] == 1
        assert location["region"]["endLine"] == 4
        assert (
            location["region"]["snippet"]["text"]
            == 'import requests\n\nrequests.get("www.google.com")\nvar = "hello"'
        )

        result2 = results[1]

        assert result2["ruleId"] == "codemodder.codemods.semgrep.sandbox-url-creation"
        assert result2["message"]["text"] == "Unbounded URL creation"

        location = result2["locations"][0]["physicalLocation"]
        assert location["artifactLocation"]["uri"] == "tests/samples/make_request.py"

        assert location["region"]["startLine"] == 3
        assert location["region"]["endLine"] == 3
        assert location["region"]["snippet"]["text"] == 'requests.get("www.google.com")'

    def _assert_secure_random_results(self, results):
        assert len(results) == 1
        result = results[0]
        assert result["ruleId"] == "codemodder.codemods.semgrep.secure-random"
        assert result["message"]["text"] == "Insecure Random"

        location = result["locations"][0]["physicalLocation"]
        assert location["artifactLocation"]["uri"] == "tests/samples/insecure_random.py"

        assert location["region"]["startLine"] == 3
        assert location["region"]["endLine"] == 3
        assert location["region"]["snippet"]["text"] == "random.random()"

    def test_two_codemods(self):
        results_by_path_and_id = semgrep_run(
            "tests/samples/",
            [
                "codemodder/codemods/semgrep/secure_random.yaml",
                "codemodder/codemods/semgrep/sandbox_url_creation.yaml",
            ],
        )

        assert sorted(results_by_path_and_id.keys()) == [
            "tests/samples/insecure_random.py",
            "tests/samples/make_request.py",
        ]

        url_sandbox_results = results_by_path_and_id["tests/samples/make_request.py"][
            "sandbox-url-creation"
        ]
        self._assert_url_sandbox_results(url_sandbox_results)

        secure_random = results_by_path_and_id["tests/samples/insecure_random.py"][
            "secure-random"
        ]
        self._assert_secure_random_results(secure_random)
