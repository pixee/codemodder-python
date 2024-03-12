import json

import pytest
import requests


@pytest.fixture(scope="module")
def codetf_schema():
    schema_path = "https://raw.githubusercontent.com/pixee/codemodder-specs/main/codetf.schema.json"
    response = requests.get(schema_path)
    yield json.loads(response.text)
