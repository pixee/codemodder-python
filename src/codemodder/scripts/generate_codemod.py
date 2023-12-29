import argparse
import pathlib


def main():
    parser = argparse.ArgumentParser(
        description="Generate skeleton files for a new codemod."
    )

    parser.add_argument("name", type=str, help="name for the new codemod")
    argv = parser.parse_args()
    codemod_id = argv.name.replace(" ", "_")
    # todo: do not continue if codemod-id is already taken

    codemodder_dir = pathlib.Path.cwd()

    core_codemods_dir = pathlib.Path(f"{codemodder_dir}/src/core_codemods")
    (core_codemods_dir / f"{codemod_id}.py").touch()

    unit_test_dir = pathlib.Path(f"{codemodder_dir}/tests/codemods")
    (unit_test_dir / f"test_{codemod_id}.py").touch()

    samples = pathlib.Path(f"{codemodder_dir}/tests/samples")
    (samples / f"{codemod_id}.py").touch()

    integration_test__dir = pathlib.Path(f"{codemodder_dir}/integration_tests")
    (integration_test__dir / f"test_{codemod_id}.py").touch()

    docs_dir = pathlib.Path(f"{codemodder_dir}/src/core_codemods/docs")
    (docs_dir / f"pixee_python_{codemod_id.replace('_', '-')}.md").touch()

    with open(
        codemodder_dir / "src/codemodder/scripts/generate_docs.py",
        "a",
        encoding="utf-8",
    ) as f:
        f.write("Update METADATA above")

    with open(
        codemodder_dir / "src/core_codemods/__init__.py", "a", encoding="utf-8"
    ) as f:
        f.write("Import and add Codemod class to registry above.")
