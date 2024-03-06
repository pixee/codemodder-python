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
