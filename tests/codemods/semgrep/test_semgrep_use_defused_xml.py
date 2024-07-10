import json

import mock

from codemodder.codemods.test import BaseSASTCodemodTest
from codemodder.dependency import DefusedXML
from core_codemods.semgrep.semgrep_use_defused_xml import SemgrepUseDefusedXml


class TestSemgrepUseDefusedXml(BaseSASTCodemodTest):
    codemod = SemgrepUseDefusedXml
    tool = "semgrep"

    def test_name(self):
        assert self.codemod.name == "use-defusedxml"

    @mock.patch("codemodder.codemods.api.FileContext.add_dependency")
    def test_etree_parse(self, add_dependency, tmpdir):
        original_code = """\
        from xml.etree.ElementTree import parse

        et = parse(user_input)
        """

        new_code = """\
        import defusedxml.ElementTree

        et = defusedxml.ElementTree.parse(user_input)
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
                                            "endColumn": 23,
                                            "endLine": 3,
                                            "snippet": {
                                                "text": "et = parse(user_input)"
                                            },
                                            "startColumn": 6,
                                            "startLine": 3,
                                        },
                                    }
                                }
                            ],
                            "message": {
                                "text": 'The native Python `xml` library is vulnerable to XML External Entity (XXE) attacks.  These attacks can leak confidential data and "XML bombs" can cause denial of service. Do not use this library to parse untrusted input. Instead  the Python documentation recommends using `defusedxml`.'
                            },
                            "ruleId": "python.lang.security.use-defused-xml-parse.use-defused-xml-parse",
                        }
                    ]
                }
            ]
        }

        self.run_and_assert(
            tmpdir,
            original_code,
            new_code,
            results=json.dumps(results),
        )
        add_dependency.assert_called_once_with(DefusedXML)
