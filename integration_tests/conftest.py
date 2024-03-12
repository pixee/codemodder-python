import json

import pytest
import requests


@pytest.fixture(scope="session")
def codetf_schema():
    schema_path = "https://raw.githubusercontent.com/pixee/codemodder-specs/main/codetf.schema.json"
    response = requests.get(schema_path, timeout=60)
    yield json.loads(response.text)
