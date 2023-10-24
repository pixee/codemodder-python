from pathlib import Path

import pytest

from codemodder.dependency import DefusedXML
from codemodder.dependency_manager import DependencyManager, Requirement


@pytest.fixture(autouse=True, scope="module")
def disable_write_dependencies():
    """Override fixture from conftest.py in order to allow testing"""


class TestDependencyManager:
    TEST_DIR = "tests/"

    def test_read_dependency_file(self, tmpdir):
        dependency_file = Path(tmpdir) / "requirements.txt"
        dependency_file.write_text("requests\n", encoding="utf-8")

        dm = DependencyManager(Path(tmpdir))
        assert dm.dependencies == {Requirement("requests"): None}

    @pytest.mark.parametrize("dry_run", [True, False])
    def test_add_dependency_preserve_comments(self, tmpdir, dry_run):
        contents = "# comment\n\nrequests\n"
        dependency_file = Path(tmpdir) / "requirements.txt"
        dependency_file.write_text(contents, encoding="utf-8")

        dm = DependencyManager(Path(tmpdir))
        dm.add([DefusedXML])
        changeset = dm.write(dry_run=dry_run)

        assert dependency_file.read_text(encoding="utf-8") == (
            contents if dry_run else "# comment\n\nrequests\ndefusedxml~=0.7.1"
        )

        assert changeset is not None
        assert changeset.path == str(dependency_file)
        assert changeset.diff == (
            "--- \n"
            "+++ \n"
            "@@ -1,3 +1,5 @@\n"
            " # comment\n"
            " \n"
            " requests\n"
            "+defusedxml~=0.7.1+\n"
        )
        assert len(changeset.changes) == 1
        assert changeset.changes[0].lineNumber == 4
        assert changeset.changes[0].description == DefusedXML.build_description()
        assert changeset.changes[0].properties == {"contextual_description": True}
