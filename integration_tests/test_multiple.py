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

    # pylint: disable=too-many-statements
    def _assert_codetf_output(self):
        with open(self.output_path, "r", encoding="utf-8") as f:
            codetf = json.load(f)

        assert sorted(codetf.keys()) == ["results", "run"]

        results = codetf["results"]
        assert len(results) == 10
        sorted_results = sorted(results, key=lambda x: x["codemod"])

        django_debug = sorted_results[0]
        assert len(django_debug["changeset"]) == 1
        assert (
            django_debug["changeset"][0]["path"]
            == "tests/samples/django-project/mysite/mysite/settings.py"
        )
        assert len(django_debug["changeset"][0]["changes"]) == 1

        django_session_cookie = sorted_results[1]
        assert len(django_session_cookie["changeset"]) == 1
        assert (
            django_session_cookie["changeset"][0]["path"]
            == "tests/samples/django-project/mysite/mysite/settings.py"
        )
        assert len(django_session_cookie["changeset"][0]["changes"]) == 1

        harden_pyyaml = sorted_results[2]
        assert len(harden_pyyaml["changeset"]) == 1
        assert harden_pyyaml["changeset"][0]["path"] == "tests/samples/unsafe_yaml.py"
        assert len(harden_pyyaml["changeset"][0]["changes"]) == 1

        limit_readline = sorted_results[3]
        assert len(limit_readline["changeset"]) == 1
        assert (
            limit_readline["changeset"][0]["path"]
            == "tests/samples/unlimited_readline.py"
        )
        assert len(limit_readline["changeset"][0]["changes"]) == 1

        process_sandbox = sorted_results[4]
        assert len(process_sandbox["changeset"]) == 1
        assert (
            process_sandbox["changeset"][0]["path"] == "tests/samples/make_process.py"
        )
        assert len(process_sandbox["changeset"][0]["changes"]) == 4

        unnecessary_f_str = sorted_results[5]
        assert len(unnecessary_f_str["changeset"]) == 1
        assert (
            unnecessary_f_str["changeset"][0]["path"]
            == "tests/samples/unnecessary_f_str.py"
        )
        assert len(unnecessary_f_str["changeset"][0]["changes"]) == 1

        secure_random = sorted_results[6]
        assert len(secure_random["changeset"]) == 1
        assert (
            secure_random["changeset"][0]["path"] == "tests/samples/insecure_random.py"
        )
        assert len(secure_random["changeset"][0]["changes"]) == 1

        remove_unused_imports = sorted_results[7]
        assert len(remove_unused_imports["changeset"]) == 1
        assert (
            remove_unused_imports["changeset"][0]["path"]
            == "tests/samples/unused_imports.py"
        )
        assert len(remove_unused_imports["changeset"][0]["changes"]) == 1

        upgrade_weak_tls = sorted_results[8]
        assert len(upgrade_weak_tls["changeset"]) == 1
        assert upgrade_weak_tls["changeset"][0]["path"] == "tests/samples/weak_tls.py"
        assert len(upgrade_weak_tls["changeset"][0]["changes"]) == 1

        url_sandbox = sorted_results[9]
        assert len(url_sandbox["changeset"]) == 1
        assert url_sandbox["changeset"][0]["path"] == "tests/samples/make_request.py"
        assert len(url_sandbox["changeset"][0]["changes"]) == 1
