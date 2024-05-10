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
                    "id": 1,
                    "title": RULE_ID,
                    "file_path": "code.py",
                    "line": 4,
                },
            ]
        }

        changes = self.run_and_assert(
            tmpdir, input_code, expected, results=json.dumps(findings)
        )

        assert changes is not None
        assert changes[0].changes[0].findings is not None
        assert changes[0].changes[0].findings[0].id == "1"
        assert changes[0].changes[0].findings[0].rule.id == RULE_ID

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
                    "id": 2,
                    "title": RULE_ID,
                    "file_path": "code.py",
                    "line": 4,
                },
            ]
        }

        changes = self.run_and_assert(
            tmpdir, input_code, expected, results=json.dumps(findings)
        )
        adds_dependency.assert_called_once_with(Fickling)

        assert changes is not None
        assert changes[0].changes[0].findings is not None
        assert changes[0].changes[0].findings[0].id == "2"
        assert changes[0].changes[0].findings[0].rule.id == RULE_ID

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
                    "id": 3,
                    "title": RULE_ID,
                    "file_path": "code.py",
                    "line": 5,
                },
                {
                    "id": 4,
                    "title": RULE_ID,
                    "file_path": "code.py",
                    "line": 6,
                },
            ]
        }

        changes = self.run_and_assert(
            tmpdir,
            input_code,
            expected,
            results=json.dumps(findings),
            num_changes=2,
        )
        adds_dependency.assert_called_once_with(Fickling)

        assert changes is not None
        assert changes[0].changes[0].findings is not None
        assert changes[0].changes[0].findings[0].id == "4"
        assert changes[0].changes[0].findings[0].rule.id == RULE_ID
        assert changes[0].changes[1].findings is not None
        assert changes[0].changes[1].findings[0].id == "3"
        assert changes[0].changes[1].findings[0].rule.id == RULE_ID

    @mock.patch("codemodder.codemods.api.FileContext.add_dependency")
    def test_pickle_loads(self, adds_dependency, tmpdir):
        input_code = (
            expected
        ) = """
        import pickle

        result = pickle.loads("data")
        """

        findings = {
            "results": [
                {
                    "id": 5,
                    "title": RULE_ID,
                    "file_path": "code.py",
                    "line": 4,
                },
            ]
        }

        self.run_and_assert(tmpdir, input_code, expected, results=json.dumps(findings))
        adds_dependency.assert_not_called()

        unfixed = self.execution_context.get_unfixed_findings(self.codemod.id)
        assert len(unfixed) == 1
        assert unfixed[0].id == "5"
        assert unfixed[0].rule.id == RULE_ID
        assert unfixed[0].lineNumber == 4
        assert unfixed[0].reason == "`fickling` does not yet support `pickle.loads`"
        assert unfixed[0].path == "code.py"
