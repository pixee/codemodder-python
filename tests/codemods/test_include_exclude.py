import pytest
from codemodder.registry import DEFAULT_EXCLUDED_CODEMODS, load_registered_codemods


class TestMatchCodemods:
    @classmethod
    def setup_class(cls):
        cls.registry = load_registered_codemods()
        cls.codemod_map = (
            cls.registry._codemods_by_name  # pylint: disable=protected-access
        )

    def test_no_include_exclude(self):
        defaults = set(
            x for x in self.registry.codemods if x.id not in DEFAULT_EXCLUDED_CODEMODS
        )
        assert set(self.registry.match_codemods(None, None)) == defaults

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
