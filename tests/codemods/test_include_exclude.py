import pytest
from codemodder.registry import DEFAULT_EXCLUDED_CODEMODS, load_registered_codemods
from core_codemods import registry


class TestMatchCodemods:
    @classmethod
    def setup_class(cls):
        cls.registry = load_registered_codemods()
        cls.codemod_map = (
            cls.registry._codemods_by_name  # pylint: disable=protected-access
        )
        cls.default_ids = [
            c().id if isinstance(c, type) else c.id for c in registry.codemods
        ]

    def test_no_include_exclude(self):
        default_codemods = set(
            x
            for x in self.registry.codemods
            if x.id in self.default_ids and x.id not in DEFAULT_EXCLUDED_CODEMODS
        )
        assert set(self.registry.match_codemods(None, None)) == default_codemods

    def test_load_sast_codemods(self):
        sast_codemods = set(
            c for c in self.registry.codemods if c.id not in self.default_ids
        )
        assert (
            set(self.registry.match_codemods(None, None, sast_only=True))
            == sast_codemods
        )

    def test_include_non_sast_in_sast(self):
        assert set(
            self.registry.match_codemods(["secure-random"], None, sast_only=True)
        ) == {self.codemod_map["secure-random"]}

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
            c
            for c in self.registry.codemods
            if c.name not in excludes and c.id in self.default_ids
        ]
