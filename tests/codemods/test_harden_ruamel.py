import pytest

from codemodder.codemods.test import BaseCodemodTest
from core_codemods.harden_ruamel import HardenRuamel


class TestHardenRuamel(BaseCodemodTest):
    codemod = HardenRuamel

    def test_name(self):
        assert self.codemod.name == "harden-ruamel"

    @pytest.mark.parametrize("loader", ["YAML()", "YAML(typ='rt')", "YAML(typ='safe')"])
    def test_safe(self, tmpdir, loader):
        input_code = f"""from ruamel.yaml import YAML
serializer = {loader}
"""
        self.run_and_assert(tmpdir, input_code, input_code)

    @pytest.mark.parametrize("loader", ["YAML(typ='base')", "YAML(typ='unsafe')"])
    def test_unsafe(self, tmpdir, loader):
        input_code = f"""from ruamel.yaml import YAML
serializer = {loader}
"""

        expected = """from ruamel.yaml import YAML
serializer = YAML(typ="safe")
"""
        self.run_and_assert(tmpdir, input_code, expected)

    @pytest.mark.parametrize(
        "loader", ["YAML(typ='base', pure=True)", "YAML(typ='unsafe', pure=True)"]
    )
    def test_unsafe_more_args(self, tmpdir, loader):
        input_code = f"""from ruamel.yaml import YAML
serializer = {loader}
"""

        expected = """from ruamel.yaml import YAML
serializer = YAML(typ="safe", pure=True)
"""
        self.run_and_assert(tmpdir, input_code, expected)

    @pytest.mark.parametrize("loader", ["YAML(typ='base')", "YAML(typ='unsafe')"])
    def test_unsafe_import(self, tmpdir, loader):
        input_code = f"""import ruamel
serializer = ruamel.yaml.{loader}
"""

        expected = """import ruamel
serializer = ruamel.yaml.YAML(typ="safe")
"""
        self.run_and_assert(tmpdir, input_code, expected)

    @pytest.mark.parametrize("loader", ["YAML(typ='base')", "YAML(typ='unsafe')"])
    def test_import_alias(self, tmpdir, loader):
        input_code = f"""from ruamel import yaml as yam
serializer = yam.{loader}
"""

        expected = """from ruamel import yaml as yam
serializer = yam.YAML(typ="safe")
"""

        self.run_and_assert(tmpdir, input_code, expected)
