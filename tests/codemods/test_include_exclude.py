import pytest
from codemodder.registry import load_registered_codemods


class TestMatchCodemods:
    @classmethod
    def setup_class(cls):
        cls.registry = load_registered_codemods()
        cls.codemod_map = (
            cls.registry._codemods_by_name  # pylint: disable=protected-access
        )

    def test_no_include_exclude(self):
        assert self.registry.match_codemods(None, None) == self.registry.codemods

    @pytest.mark.parametrize(
        "input_str", ["secure-random", "secure-random,url-sandbox"]
    )
    def test_include(self, input_str):
        includes = input_str.split(",")
        assert self.registry.match_codemods(includes, None) == [
            self.codemod_map[name] for name in includes
        ]

    @pytest.mark.parametrize(
        "input_str", ["url-sandbox,secure-random", "secure-random,url-sandbox"]
    )
    def test_include_preserve_order(self, input_str):
        includes = input_str.split(",")
        assert [
            codemod.name for codemod in self.registry.match_codemods(includes, None)
        ] == includes

    @pytest.mark.parametrize(
        "input_str",
        [
            "secure-random",
            "secure-random,url-sandbox",
        ],
    )
    def test_exclude(self, input_str):
        excludes = input_str.split(",")
        assert self.registry.match_codemods(None, excludes) == [
            v for (k, v) in self.codemod_map.items() if k not in excludes
        ]
