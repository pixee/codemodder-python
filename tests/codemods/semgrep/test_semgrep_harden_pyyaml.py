import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.semgrep.semgrep_harden_pyyaml import SemgrepHardenPyyaml


class TestSemgrepHardenPyyaml(BaseSASTCodemodTest):
    codemod = SemgrepHardenPyyaml
    tool = "semgrep"

    def test_name(self):
        assert self.codemod.name == "harden-pyyaml"

    def test_pyyaml(self, tmpdir):
        input_code = """\
        import yaml
        data = b'!!python/object/apply:subprocess.Popen \\n- ls'
        deserialized_data = yaml.load(data, Loader=yaml.Loader)
        """
        expected_output = """\
        import yaml
        data = b'!!python/object/apply:subprocess.Popen \\n- ls'
        deserialized_data = yaml.load(data, Loader=yaml.SafeLoader)
        """

        results = {
            "runs": [
                {
                    "results": [
                        {
                            "fingerprints": {"matchBasedId/v1": "123"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": "code.py",
                                            "uriBaseId": "%SRCROOT%",
                                        },
                                        "region": {
                                            "endColumn": 56,
                                            "endLine": 3,
                                            "snippet": {
                                                "text": "deserialized_data = yaml.load(data, Loader=yaml.Loader)"
                                            },
                                            "startColumn": 21,
                                            "startLine": 3,
                                        },
                                    }
                                }
                            ],
                            "message": {
                                "text": "Detected a possible YAML deserialization vulnerability. `yaml.unsafe_load`, `yaml.Loader`, `yaml.CLoader`, and `yaml.UnsafeLoader` are all known to be unsafe methods of deserializing YAML. An attacker with control over the YAML input could create special YAML input that allows the attacker to run arbitrary Python code. This would allow the attacker to steal files, download and install malware, or otherwise take over the machine. Use `yaml.safe_load` or `yaml.SafeLoader` instead."
                            },
                            "properties": {},
                            "ruleId": "python.lang.security.deserialization.avoid-pyyaml-load.avoid-pyyaml-load",
                        }
                    ]
                }
            ]
        }
        self.run_and_assert(
            tmpdir,
            input_code,
            expected_output,
            results=json.dumps(results),
        )

    def test_pyyaml_django(self, tmpdir):
        input_code = """\
        import yaml
        
        def index(request):
            cookie = request.cookies.get('cookie')
            return "Hey there! {}!".format(yaml.load(cookie))
        """
        expected_output = """\
        import yaml
        
        def index(request):
            cookie = request.cookies.get('cookie')
            return "Hey there! {}!".format(yaml.load(cookie, Loader=yaml.SafeLoader))
        """

        results = {
            "runs": [
                {
                    "results": [
                        {
                            "fingerprints": {"matchBasedId/v1": "123"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": "code.py",
                                            "uriBaseId": "%SRCROOT%",
                                        },
                                        "region": {
                                            "endColumn": 53,
                                            "endLine": 5,
                                            "snippet": {
                                                "text": '    return "Hey there! {}!".format(yaml.load(cookie))'
                                            },
                                            "startColumn": 36,
                                            "startLine": 5,
                                        },
                                    }
                                }
                            ],
                            "message": {
                                "text": "Avoid using insecure deserialization library, backed by `pickle`, `_pickle`, `cpickle`, `dill`, `shelve`, or `yaml`, which are known to lead to remote code execution vulnerabilities."
                            },
                            "properties": {},
                            "ruleId": "python.django.security.audit.avoid-insecure-deserialization.avoid-insecure-deserialization",
                        }
                    ]
                }
            ]
        }
        self.run_and_assert(
            tmpdir,
            input_code,
            expected_output,
            results=json.dumps(results),
        )
