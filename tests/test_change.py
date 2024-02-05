import pytest

from codemodder.change import Change, ChangeSet, DiffSide


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

    result = changeset.to_json()

    assert result["path"] == "test"
    assert result["diff"] == diff
    assert result["changes"][0]["lineNumber"] == str(1)
    assert result["changes"][0]["description"] == "Change 1 to 2"
    assert result["changes"][0]["diffSide"] == "right"
    assert result["changes"][0]["properties"] == {}
    assert result["changes"][0]["packageActions"] == []


@pytest.mark.parametrize("side", [DiffSide.LEFT, DiffSide.RIGHT])
def test_change_diffside(side):
    change = Change(
        lineNumber=1,
        description="Change 1 to 2",
        diffSide=side,
    )

    assert change.diffSide == side
    assert change.to_json()["diffSide"] == side.value
