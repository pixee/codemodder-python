from pathlib import Path

import pytest

from codemodder.dependency import DefusedXML, Security
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
        assert dm.dependencies == {"requests": Requirement("requests")}

    @pytest.mark.parametrize("dry_run", [True, False])
    def test_add_dependency_preserve_comments(self, tmpdir, dry_run):
        contents = "# comment\n\nrequests\n"
        dependency_file = Path(tmpdir) / "requirements.txt"
        dependency_file.write_text(contents, encoding="utf-8")

        dm = DependencyManager(Path(tmpdir))
        dm.add([DefusedXML])
        changeset = dm.write(dry_run=dry_run)

        assert dependency_file.read_text(encoding="utf-8") == (
            contents if dry_run else "# comment\n\nrequests\ndefusedxml~=0.7.1\n"
        )

        assert changeset is not None
        assert changeset.path == dependency_file.name
        assert changeset.diff == (
            "--- \n"
            "+++ \n"
            "@@ -1,3 +1,4 @@\n"
            " # comment\n"
            " \n"
            " requests\n"
            "+defusedxml~=0.7.1\n"
        )
        assert len(changeset.changes) == 1
        assert changeset.changes[0].lineNumber == 4
        assert changeset.changes[0].description == DefusedXML.build_description()
        assert changeset.changes[0].properties == {
            "contextual_description": True,
            "contextual_description_position": "right",
        }

    def test_add_multiple_dependencies(self, tmpdir):
        dependency_file = Path(tmpdir) / "requirements.txt"
        dependency_file.write_text("requests\n", encoding="utf-8")

        for dep in [DefusedXML, Security]:
            dm = DependencyManager(Path(tmpdir))
            dm.add([dep])
            dm.write()

        assert dependency_file.read_text(encoding="utf-8") == (
            "requests\ndefusedxml~=0.7.1\nsecurity~=1.2.0\n"
        )

    def test_add_same_dependency_only_once(self, tmpdir):
        dependency_file = Path(tmpdir) / "requirements.txt"
        dependency_file.write_text("requests\n", encoding="utf-8")

        for dep in [Security, Security]:
            dm = DependencyManager(Path(tmpdir))
            dm.add([dep])
            dm.write()

        assert dependency_file.read_text(encoding="utf-8") == (
            "requests\nsecurity~=1.2.0\n"
        )

    @pytest.mark.parametrize("version", ["1.2.0", "1.0.1"])
    def test_dont_add_existing_dependency(self, version, tmpdir):
        dependency_file = Path(tmpdir) / "requirements.txt"
        dependency_file.write_text(f"requests\nsecurity~={version}\n", encoding="utf-8")

        dm = DependencyManager(Path(tmpdir))
        dm.add([Security])
        dm.write()

        assert dependency_file.read_text(encoding="utf-8") == (
            f"requests\nsecurity~={version}\n"
        )

    def test_dependency_file_no_terminating_newline(self, tmpdir):
        dependency_file = Path(tmpdir) / "requirements.txt"
        dependency_file.write_text("requests\nwhatever", encoding="utf-8")

        dm = DependencyManager(Path(tmpdir))
        dm.add([Security])
        changeset = dm.write()

        assert changeset is not None
        assert changeset.diff == (
            "--- \n"
            "+++ \n"
            "@@ -1,2 +1,3 @@\n"
            " requests\n"
            "-whatever\n"
            "+whatever\n"
            "+security~=1.2.0\n"
        )

        assert dependency_file.read_text(encoding="utf-8") == (
            "requests\nwhatever\nsecurity~=1.2.0\n"
        )
