import json
import subprocess
from integration_tests.base_test import CleanRepoMixin


class TestMultipleCodemodsRun(CleanRepoMixin):
    output_path = "test-codetf.txt"

    def test_codetf_output(self):
        """Tests expected codetf output when all default codemods run."""
        command = [
            "python",
            "-m",
            "codemodder",
            "tests/samples/",
            "--output",
            self.output_path,
        ]

        completed_process = subprocess.run(
            command,
            check=False,
        )
        assert completed_process.returncode == 0
        self._assert_codetf_output()

    def _assert_codetf_output(self):
        with open(self.output_path, "r", encoding="utf-8") as f:
            codetf = json.load(f)

        assert sorted(codetf.keys()) == ["results", "run"]

        results = codetf["results"]
        assert len(results) == 3
        sorted_results = sorted(results, key=lambda x: x["codemod"])

        process_sandbox = sorted_results[0]
        assert len(process_sandbox["changeset"]) == 1
        assert (
            process_sandbox["changeset"][0]["path"] == "tests/samples/make_process.py"
        )
        assert len(process_sandbox["changeset"][0]["changes"]) == 4

        secure_random = sorted_results[1]
        assert len(secure_random["changeset"]) == 1
        assert (
            secure_random["changeset"][0]["path"] == "tests/samples/insecure_random.py"
        )
        assert len(secure_random["changeset"][0]["changes"]) == 1

        url_sandbox = sorted_results[2]
        assert len(url_sandbox["changeset"]) == 1
        assert url_sandbox["changeset"][0]["path"] == "tests/samples/make_request.py"
        assert len(url_sandbox["changeset"][0]["changes"]) == 1
