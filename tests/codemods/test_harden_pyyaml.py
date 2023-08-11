import pytest
from codemodder.codemods.harden_pyyaml import HardenPyyaml, UNSAFE_LOADERS
from tests.codemods.base_codemod_test import BaseSemgrepCodemodTest


class TestHardenPyyaml(BaseSemgrepCodemodTest):
    codemod = HardenPyyaml

    def test_rule_ids(self):
        assert self.codemod.RULE_IDS == ["harden-pyyaml"]

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

    @pytest.mark.skip()
    def test_import_alias(self, tmpdir):
        input_code = """import yaml as yam
from yaml import Loader

data = b'!!python/object/apply:subprocess.Popen \\n- ls'
deserialized_data = yam.load(data, Loader=Loader)
"""
        expected = """import yaml
data = b'!!python/object/apply:subprocess.Popen \\n- ls'
deserialized_data = yaml.load(data, yaml.SafeLoader)
"""
        self.run_and_assert(tmpdir, input_code, expected)
