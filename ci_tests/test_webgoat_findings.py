import json

import pytest


EXPECTED_FINDINGS = [
    "pixee:python/order-imports",
    "pixee:python/secure-random",
    "pixee:python/sandbox-process-creation",
    "pixee:python/unused-imports",
    "pixee:python/django-session-cookie-secure-off",
    "pixee:python/harden-pyyaml",
    "pixee:python/django-debug-flag-on",
    "pixee:python/url-sandbox",
]


@pytest.fixture(scope="session")
def webgoat_findings():
    with open("output.codetf") as ff:
        results = json.load(ff)

    yield set([x["codemod"] for x in results["results"]])


def test_num_webgoat_findings(webgoat_findings):
    assert len(webgoat_findings) == len(EXPECTED_FINDINGS)


@pytest.mark.parametrize("finding", EXPECTED_FINDINGS)
def test_webgoat_findings(webgoat_findings, finding):
    assert finding in webgoat_findings
