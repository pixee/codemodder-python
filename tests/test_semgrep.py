import json
from pathlib import Path

import pytest

from codemodder.codemods.semgrep import SemgrepSarifFileDetector
from codemodder.context import CodemodExecutionContext
from codemodder.semgrep import SemgrepResultSet, SemgrepSarifToolDetector

SAMPLE_DATA_PATH = Path(__file__).parent / "samples"


@pytest.mark.parametrize(
    "filename, expected",
    [
        ("pygoat.semgrep.sarif.json", True),
        ("webgoat_v8.2.0_codeql.sarif", False),
    ],
)
def test_semgrep_sarif_tool_detector(filename, expected):
    detector = SemgrepSarifToolDetector()
    sarif_path = SAMPLE_DATA_PATH / filename
    data = json.load(sarif_path.open())
    assert detector.detect(data["runs"][0]) is expected


def test_semgrep_sarif_codemode_detector(mocker):
    detector = SemgrepSarifFileDetector()

    context = mocker.MagicMock(spec=CodemodExecutionContext)
    context.tool_result_files_map = {
        "semgrep": [SAMPLE_DATA_PATH / "pygoat.semgrep.sarif.json"]
    }
    results = detector.apply(codemod_id="foo", context=context, files_to_analyze=[])
    assert isinstance(results, SemgrepResultSet)
    assert len(results) == 25
    assert (
        "python.django.security.audit.secure-cookies.django-secure-set-cookie"
        in results
    )
