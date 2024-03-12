import json

import pytest
from security import safe_requests


@pytest.fixture(scope="session")
def codetf_schema():
    schema_path = "https://raw.githubusercontent.com/pixee/codemodder-specs/main/codetf.schema.json"
    response = safe_requests.get(schema_path, timeout=60)
    yield json.loads(response.text)
