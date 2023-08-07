from collections import defaultdict
from pathlib import Path
import pytest
import libcst as cst
from libcst.codemod import CodemodContext
from codemodder.codemods.harden_pyyaml import HardenPyyaml, UNSAFE_LOADERS
from codemodder.file_context import FileContext
from codemodder.semgrep import run_on_directory as semgrep_run
from codemodder.semgrep import find_all_yaml_files


class TestHardenPyyaml:
    def results_by_id(self, input_code, tmpdir):
        tmp_file_path = tmpdir / "code.py"
        with open(tmp_file_path, "w", encoding="utf-8") as tmp_file:
            tmp_file.write(input_code)

        return semgrep_run(
            find_all_yaml_files({HardenPyyaml.METADATA.NAME: HardenPyyaml}), tmpdir
        )

    def run_and_assert(self, tmpdir, input_code, expected):
        input_tree = cst.parse_module(input_code)
        results = self.results_by_id(input_code, tmpdir)[tmpdir / "code.py"]
        print(results)
        file_context = FileContext(
            tmpdir / "code.py",
            False,
            [],
            [],
            results,
        )
        command_instance = HardenPyyaml(CodemodContext(), file_context)
        output_tree = command_instance.transform_module(input_tree)

        assert output_tree.code == expected

    def test_rule_ids(self):
        assert HardenPyyaml.RULE_IDS == ["harden-pyyaml"]

    def test_with_empty_results(self):
        input_code = """import yaml
data = b'!!python/object/apply:subprocess.Popen \\n- ls'
deserialized_data = yaml.load(data, Loader=Loader)"""
        input_tree = cst.parse_module(input_code)
        file_context = FileContext(Path(""), False, [], [], defaultdict(list))
        command_instance = HardenPyyaml(CodemodContext(), file_context)
        output_tree = command_instance.transform_module(input_tree)

        assert output_tree.code == input_code

    def test_safe_loader(self, tmpdir):
        input_code = """import yaml
data = b'!!python/object/apply:subprocess.Popen \\n- ls'
deserialized_data = yaml.load(data, Loader=yaml.SafeLoader)
"""
        self.run_and_assert(tmpdir, input_code, input_code)

    @pytest.mark.parametrize("loader", UNSAFE_LOADERS)
    def test_all_unsafe_loaders_arg(self, tmpdir, loader):
        input_code = f"""import yaml
data = b'!!python/object/apply:subprocess.Popen \\n- ls'
deserialized_data = yaml.load(data, yaml.{loader})
"""

        expected = """import yaml
data = b'!!python/object/apply:subprocess.Popen \\n- ls'
deserialized_data = yaml.load(data, yaml.SafeLoader)
"""
        self.run_and_assert(tmpdir, input_code, expected)

    @pytest.mark.parametrize("loader", UNSAFE_LOADERS)
    def test_all_unsafe_loaders_kwarg(self, tmpdir, loader):
        input_code = f"""import yaml
data = b'!!python/object/apply:subprocess.Popen \\n- ls'
deserialized_data = yaml.load(data, Loader=yaml.{loader})
"""

        expected = """import yaml
data = b'!!python/object/apply:subprocess.Popen \\n- ls'
deserialized_data = yaml.load(data, yaml.SafeLoader)
"""
        self.run_and_assert(tmpdir, input_code, expected)
