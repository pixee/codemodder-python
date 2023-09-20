import pytest
from codemodder.registry import load_registered_codemods


class TestMatchCodemods:
    @classmethod
    def setup_class(cls):
        cls.registry = load_registered_codemods()
        cls.codemod_map = {
            codemod.name: codemod
            for codemod in cls.registry._codemods  # pylint: disable=protected-access
        }

    def test_no_include_exclude(self):
        assert self.registry.match_codemods(None, None) == self.codemod_map

    @pytest.mark.parametrize(
        "input_str", ["secure-random", "secure-random,url-sandbox"]
    )
    def test_include(self, input_str):
        assert self.registry.match_codemods(input_str, None) == {
            name: self.codemod_map[name] for name in input_str.split(",")
        }

    @pytest.mark.parametrize(
        "input_str",
        [
            "secure-random",
            "secure-random,url-sandbox",
        ],
    )
    def test_exclude(self, input_str):
        assert self.registry.match_codemods(None, input_str) == {
            k: v for (k, v) in self.codemod_map.items() if k not in input_str.split(",")
        }
