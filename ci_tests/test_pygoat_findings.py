import json

import pytest

EXPECTED_FINDINGS = [
    "pixee:python/add-requests-timeouts",
    "pixee:python/secure-random",
    "pixee:python/sandbox-process-creation",
    "pixee:python/django-session-cookie-secure-off",
    "pixee:python/harden-pyyaml",
    "pixee:python/django-debug-flag-on",
    "pixee:python/url-sandbox",
    "pixee:python/use-defusedxml",
    "pixee:python/use-walrus-if",
]


@pytest.fixture(scope="session")
def pygoat_findings():
    with open("output.codetf") as ff:
        results = json.load(ff)

    yield set([x["codemod"] for x in results["results"] if x["changeset"]])


def test_num_pygoat_findings(pygoat_findings):
    assert len(pygoat_findings) == len(EXPECTED_FINDINGS)


@pytest.mark.parametrize("finding", EXPECTED_FINDINGS)
def test_pygoat_findings(pygoat_findings, finding):
    assert finding in pygoat_findings
