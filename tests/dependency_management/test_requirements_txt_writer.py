from pathlib import Path

import pytest

from codemodder.codetf import DiffSide
from codemodder.dependency import DefusedXML, Requirement, Security
from codemodder.dependency_management.requirements_txt_writer import (
    RequirementsTxtWriter,
)
from codemodder.project_analysis.file_parsers.package_store import (
    FileType,
    PackageStore,
)


class TestRequirementsTxtWriter:
    @pytest.mark.parametrize("dry_run", [True, False])
    def test_add_dependencies_preserve_comments(self, tmpdir, dry_run):
        contents = "# comment\n\nrequests\n"
        dependency_file = Path(tmpdir) / "requirements.txt"
        dependency_file.write_text(contents, encoding="utf-8")
        store = PackageStore(
            type=FileType.REQ_TXT,
            file=dependency_file,
            dependencies=set(),
            py_versions=[],
        )
        writer = RequirementsTxtWriter(store, Path(tmpdir))
        dependencies = [DefusedXML, Security]
        changeset = writer.write(dependencies, dry_run=dry_run)

        assert dependency_file.read_text(encoding="utf-8") == (
            contents
            if dry_run
            else (
                "# comment\n\nrequests\n"
                + f"{DefusedXML.requirement}\n"
                + f"{Security.requirement}\n"
            )
        )

        assert changeset is not None
        assert changeset.path == dependency_file.name

        assert changeset.diff == (
            "--- \n"
            "+++ \n"
            "@@ -1,3 +1,5 @@\n"
            " # comment\n"
            " \n"
            " requests\n"
            f"+{DefusedXML.requirement}\n"
            f"+{Security.requirement}\n"
        )
        assert len(changeset.changes) == 2
        change_one = changeset.changes[0]
        assert change_one.lineNumber == 4
        assert change_one.description == DefusedXML.build_description()
        assert change_one.diffSide == DiffSide.RIGHT
        assert change_one.properties == {
            "contextual_description": True,
            "contextual_description_position": "right",
        }
        change_two = changeset.changes[1]
        assert change_two.lineNumber == 5
        assert change_two.description == Security.build_description()
        assert change_two.diffSide == DiffSide.RIGHT
        assert change_two.properties == {
            "contextual_description": True,
            "contextual_description_position": "right",
        }

    def test_add_same_dependency_only_once(self, tmpdir):
        dependency_file = Path(tmpdir) / "requirements.txt"
        dependency_file.write_text("requests\n", encoding="utf-8")

        store = PackageStore(
            type=FileType.REQ_TXT,
            file=dependency_file,
            dependencies=set(),
            py_versions=[],
        )
        writer = RequirementsTxtWriter(store, Path(tmpdir))
        dependencies = [Security, Security]
        changeset = writer.write(dependencies)
        assert len(changeset.changes) == 1

        assert dependency_file.read_text(encoding="utf-8") == (
            f"requests\n{Security.requirement}\n"
        )

    def test_dont_add_existing_dependency(self, tmpdir):
        dependency_file = Path(tmpdir) / "requirements.txt"
        contents = f"requests\n{Security.requirement}\n"
        dependency_file.write_text(contents, encoding="utf-8")

        store = PackageStore(
            type=FileType.REQ_TXT,
            file=dependency_file,
            dependencies={Security.requirement},
            py_versions=[],
        )
        writer = RequirementsTxtWriter(store, Path(tmpdir))
        dependencies = [Security]
        changeset = writer.write(dependencies)
        assert changeset is None
        assert dependency_file.read_text(encoding="utf-8") == contents

    def test_dont_add_existing_dependency_with_different_version(self, tmpdir):
        """This is dependabot's job, not ours"""
        dependency_file = Path(tmpdir) / "requirements.txt"

        existing_requirement = "defusedxml==1.1.0"
        contents = f"requests\n{existing_requirement}\n"
        dependency_file.write_text(contents, encoding="utf-8")

        store = PackageStore(
            type=FileType.REQ_TXT,
            file=dependency_file,
            dependencies={Requirement(existing_requirement)},
            py_versions=[],
        )
        writer = RequirementsTxtWriter(store, Path(tmpdir))
        dependencies = [DefusedXML]
        changeset = writer.write(dependencies)
        assert changeset is None
        assert dependency_file.read_text(encoding="utf-8") == contents

    def test_dependency_file_no_terminating_newline(self, tmpdir):
        contents = "# comment\n\nrequests"
        dependency_file = Path(tmpdir) / "requirements.txt"
        dependency_file.write_text(contents, encoding="utf-8")

        store = PackageStore(
            type=FileType.REQ_TXT,
            file=dependency_file,
            dependencies=set(),
            py_versions=[],
        )
        writer = RequirementsTxtWriter(store, Path(tmpdir))
        dependencies = [DefusedXML, Security]
        changeset = writer.write(dependencies)

        assert (
            dependency_file.read_text(encoding="utf-8")
            == "# comment\n\nrequests\n"
            + f"{DefusedXML.requirement}\n"
            + f"{Security.requirement}\n"
        )

        assert changeset is not None
        assert changeset.path == dependency_file.name

        assert changeset.diff == (
            "--- \n"
            "+++ \n"
            "@@ -1,3 +1,5 @@\n"
            " # comment\n"
            " \n"
            " requests\n"
            f"+{DefusedXML.requirement}\n"
            f"+{Security.requirement}\n"
        )
