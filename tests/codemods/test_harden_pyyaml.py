import pytest
import yaml
from core_codemods.harden_pyyaml import HardenPyyaml
from tests.codemods.base_codemod_test import BaseSemgrepCodemodTest

UNSAFE_LOADERS = yaml.loader.__all__.copy()  # type: ignore
UNSAFE_LOADERS.remove("SafeLoader")


class TestHardenPyyaml(BaseSemgrepCodemodTest):
    codemod = HardenPyyaml

    def test_name(self):
        assert self.codemod.name() == "harden-pyyaml"

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
deserialized_data = yaml.load(data, Loader=yaml.SafeLoader)
"""
        self.run_and_assert(tmpdir, input_code, expected)

    def test_import_alias(self, tmpdir):
        input_code = """import yaml as yam
from yaml import Loader

data = b'!!python/object/apply:subprocess.Popen \\n- ls'
deserialized_data = yam.load(data, Loader=Loader)
"""
        expected = """import yaml as yam
from yaml import Loader

data = b'!!python/object/apply:subprocess.Popen \\n- ls'
deserialized_data = yam.load(data, Loader=yam.SafeLoader)
"""
        self.run_and_assert(tmpdir, input_code, expected)

    def test_preserve_custom_loader(self, tmpdir):
        expected = input_code = """
        import yaml
        from custom import CustomLoader

        yaml.load(data, CustomLoader)
        """

        self.run_and_assert(tmpdir, input_code, expected)

    def test_preserve_custom_loader_kwarg(self, tmpdir):
        expected = input_code = """
        import yaml
        from custom import CustomLoader

        yaml.load(data, Loader=CustomLoader)
        """

        self.run_and_assert(tmpdir, input_code, expected)
