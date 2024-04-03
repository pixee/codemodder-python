import json

import mock

from codemodder.codemods.test import BaseSASTCodemodTest
from codemodder.dependency import Fickling
from core_codemods.defectdojo.semgrep.avoid_insecure_deserialization import (
    AvoidInsecureDeserialization,
)

RULE_ID = "python.django.security.audit.avoid-insecure-deserialization.avoid-insecure-deserialization"


class TestDjangoAvoidInsecureDeserialization(BaseSASTCodemodTest):
    codemod = AvoidInsecureDeserialization
    tool = "defectdojo"

    def test_name(self):
        assert self.codemod._metadata.name == "avoid-insecure-deserialization"

    def test_yaml_load(self, tmpdir):
        input_code = """
        import yaml

        result = yaml.load("data")
        """
        expected = """
        import yaml

        result = yaml.load("data", Loader=yaml.SafeLoader)
        """

        findings = {
            "results": [
                {
                    "title": RULE_ID,
                    "file_path": "code.py",
                    "line": 4,
                },
            ]
        }

        self.run_and_assert(tmpdir, input_code, expected, results=json.dumps(findings))

    @mock.patch("codemodder.codemods.api.FileContext.add_dependency")
    def test_pickle_load(self, adds_dependency, tmpdir):
        input_code = """
        import pickle

        result = pickle.load("data")
        """
        expected = """
        import fickling

        result = fickling.load("data")
        """

        findings = {
            "results": [
                {
                    "title": RULE_ID,
                    "file_path": "code.py",
                    "line": 4,
                },
            ]
        }

        self.run_and_assert(tmpdir, input_code, expected, results=json.dumps(findings))
        adds_dependency.assert_called_once_with(Fickling)

    @mock.patch("codemodder.codemods.api.FileContext.add_dependency")
    def test_pickle_and_yaml(self, adds_dependency, tmpdir):
        input_code = """
        import pickle
        import yaml

        result = pickle.load("data")
        result = yaml.load("data")
        """
        expected = """
        import yaml
        import fickling

        result = fickling.load("data")
        result = yaml.load("data", Loader=yaml.SafeLoader)
        """

        findings = {
            "results": [
                {
                    "title": RULE_ID,
                    "file_path": "code.py",
                    "line": 5,
                },
                {
                    "title": RULE_ID,
                    "file_path": "code.py",
                    "line": 6,
                },
            ]
        }

        self.run_and_assert(
            tmpdir,
            input_code,
            expected,
            results=json.dumps(findings),
            num_changes=2,
        )
        adds_dependency.assert_called_once_with(Fickling)
