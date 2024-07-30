import json
from pathlib import Path

import jsonschema
import pytest
import requests

from codemodder.codetf import Change, ChangeSet, CodeTF, DiffSide, Reference, Result


@pytest.fixture(autouse=True)
def disable_write_report():
    """
    Override conftest to enable results to be written to disk for these tests.
    """


@pytest.fixture(autouse=True, scope="module")
def codetf_schema():
    schema_path = "https://raw.githubusercontent.com/pixee/codemodder-specs/main/codetf.schema.json"
    response = requests.get(schema_path)
    yield json.loads(response.text)


def test_change():
    diff = "--- a/test\n+++ b/test\n@@ -1,1 +1,1 @@\n-1\n+2\n"
    changeset = ChangeSet(
        path="test",
        diff=diff,
        changes=[
            Change(
                lineNumber=1,
                description="Change 1 to 2",
            ),
        ],
    )

    result = changeset.model_dump()

    assert result["path"] == "test"
    assert result["diff"] == diff
    assert result["changes"][0]["lineNumber"] == 1
    assert result["changes"][0]["description"] == "Change 1 to 2"
    assert result["changes"][0]["diffSide"] == DiffSide.RIGHT
    assert result["changes"][0]["properties"] is None
    assert result["changes"][0]["packageActions"] is None


@pytest.mark.parametrize("side", [DiffSide.LEFT, DiffSide.RIGHT])
def test_change_diffside(side):
    change = Change(
        lineNumber=1,
        description="Change 1 to 2",
        diffSide=side,
    )

    assert change.diffSide == side
    assert change.model_dump()["diffSide"] == side


def test_change_invalid_line_number():
    with pytest.raises(ValueError):
        Change(lineNumber=0, description="Change 1 to 2")


def test_write_codetf(tmpdir, mocker, codetf_schema):
    path = tmpdir / "test.codetf.json"

    assert not path.exists()

    context = mocker.MagicMock(directory=Path("/foo/bar/whatever"))
    codetf = CodeTF.build(context, 42, [], [])
    retval = codetf.write_report(path)

    assert retval == 0
    assert path.exists()

    data = path.read_text(encoding="utf-8")
    CodeTF.model_validate_json(data)

    jsonschema.validate(json.loads(data), codetf_schema)


def test_write_codetf_with_results(tmpdir, mocker, codetf_schema):
    path = tmpdir / "test.codetf.json"

    assert not path.exists()

    context = mocker.MagicMock(directory=Path("/foo/bar/whatever"))
    results = [
        Result(
            codemod="test",
            summary="test",
            description="test",
            changeset=[
                ChangeSet(
                    path="test",
                    diff="--- a/test\n+++ b/test\n@@ -1,1 +1,1 @@\n-1\n+2\n",
                    changes=[
                        Change(
                            lineNumber=1,
                            description="Change 1 to 2",
                        ),
                    ],
                ),
            ],
        )
    ]
    codetf = CodeTF.build(context, 42, [], results)
    retval = codetf.write_report(path)

    assert retval == 0
    assert path.exists()

    data = path.read_text(encoding="utf-8")
    CodeTF.model_validate_json(data)

    jsonschema.validate(json.loads(data), codetf_schema)


def test_reference_use_url_for_description():
    ref = Reference(url="https://example.com")
    assert ref.description == "https://example.com"
