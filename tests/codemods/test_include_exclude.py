import pytest

from codemodder.registry import DEFAULT_EXCLUDED_CODEMODS, load_registered_codemods
from core_codemods import registry


class TestMatchCodemods:
    @classmethod
    def setup_class(cls):
        cls.registry = load_registered_codemods()
        cls.codemod_map = cls.registry._codemods_by_id
        cls.all_ids = [
            c().id if isinstance(c, type) else c.id for c in registry.codemods
        ]

    def test_no_include_exclude(self):
        assert set(self.registry.match_codemods(None, None)) == set(
            x
            for x in self.registry.codemods
            if x.id in self.all_ids and x.id not in DEFAULT_EXCLUDED_CODEMODS
        )

    def test_load_sast_codemods(self):
        sast_codemods = set(
            c for c in self.registry.codemods if c.id not in self.all_ids
        )
        assert (
            set(self.registry.match_codemods(None, None, sast_only=True))
            == sast_codemods
        )

    def test_include_non_sast_in_sast(self):
        assert set(
            self.registry.match_codemods(
                ["pixee:python/secure-random"], None, sast_only=True
            )
        ) == {self.codemod_map["pixee:python/secure-random"]}

    @pytest.mark.parametrize(
        "input_str",
        [
            "pixee:python/secure-random",
            "pixee:python/secure-random,pixee:python/url-sandbox",
        ],
    )
    def test_include(self, input_str):
        includes = input_str.split(",")
        assert self.registry.match_codemods(includes, None) == [
            self.codemod_map[name] for name in includes
        ]

    @pytest.mark.parametrize(
        "input_str",
        [
            "pixee:python/url-sandbox,pixee:python/secure-random",
            "pixee:python/secure-random,pixee:python/url-sandbox",
        ],
    )
    def test_include_preserve_order(self, input_str):
        includes = input_str.split(",")
        assert [
            codemod.id for codemod in self.registry.match_codemods(includes, None)
        ] == includes

    @pytest.mark.parametrize(
        "input_str",
        [
            "pixee:python/secure-random",
            "pixee:python/secure-random,pixee:python/url-sandbox",
        ],
    )
    def test_exclude(self, input_str):
        excludes = input_str.split(",")
        res = [
            c
            for c in self.registry.codemods
            if c.id in self.all_ids and c.id not in excludes
        ]
        assert self.registry.match_codemods(None, excludes) == res

    def test_bad_codemod_include_no_match(self):
        assert self.registry.match_codemods(["doesntexist"], None) == []

    def test_codemod_include_some_match(self):
        assert self.registry.match_codemods(
            ["doesntexist", "pixee:python/secure-random"], None
        ) == [self.codemod_map["pixee:python/secure-random"]]

    def test_bad_codemod_exclude_all_match(self):
        assert self.registry.match_codemods(None, ["doesntexist"]) == [
            c for c in self.registry.codemods if c.id in self.all_ids
        ]

    def test_exclude_some_match(self):
        assert self.registry.match_codemods(
            None, ["doesntexist", "pixee:python/secure-random"]
        ) == [
            c
            for c in self.registry.codemods
            if c.id not in "pixee:python/secure-random" and c.id in self.all_ids
        ]

    def test_include_with_pattern(self):
        assert self.registry.match_codemods(["*django*"], None) == [
            c for c in self.registry.codemods if "django" in c.id
        ]

    def test_include_with_pattern_and_another(self):
        assert self.registry.match_codemods(
            ["*django*", "pixee:python/use-defusedxml"], None
        ) == [c for c in self.registry.codemods if "django" in c.id] + [
            self.codemod_map["pixee:python/use-defusedxml"]
        ]

    def test_include_sast_with_prefix(self):
        assert self.registry.match_codemods(["sonar*"], None, sast_only=False) == [
            c for c in self.registry.codemods if c.origin == "sonar"
        ]

    def test_warn_pattern_no_match(self, caplog):
        assert self.registry.match_codemods(["*doesntexist*"], None) == []
        assert (
            "Given codemod pattern '*doesntexist*' does not match any codemods"
            in caplog.text
        )

    def test_exclude_with_pattern(self):
        assert self.registry.match_codemods(None, ["*django*"], sast_only=False) == [
            c
            for c in self.registry.codemods
            if "django" not in c.id and c.id in self.all_ids
        ]

    def test_exclude_with_pattern_and_another(self):
        assert self.registry.match_codemods(
            None, ["*django*", "pixee:python/use-defusedxml"], sast_only=False
        ) == [
            c
            for c in self.registry.codemods
            if "django" not in c.id
            and c.id in self.all_ids
            and c.id != "pixee:python/use-defusedxml"
        ]

    def test_exclude_pixee_with_prefix(self):
        assert self.registry.match_codemods(None, ["pixee*"], sast_only=False) == [
            c
            for c in self.registry.codemods
            if not c.origin == "pixee" and c.id in self.all_ids
        ]
