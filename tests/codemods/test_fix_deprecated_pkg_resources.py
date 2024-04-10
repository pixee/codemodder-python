import pytest

from codemodder.codemods.test import BaseSemgrepCodemodTest
from core_codemods.fix_deprecated_pkg_resources import FixDeprecatedPkgResources


class TestFixDeprecatedPkgResources(BaseSemgrepCodemodTest):
    codemod = FixDeprecatedPkgResources

    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """
                import pkg_resources
                dist = pkg_resources.get_distribution("package_name")
                """,
                """
                from importlib.metadata import distribution

                dist = distribution("package_name")
                """,
            ),
            (
                """
                import pkg_resources
                version = pkg_resources.get_distribution("package_name").version
                """,
                """
                from importlib.metadata import distribution

                version = distribution("package_name").version
                """,
            ),
        ],
    )
    def test_import(self, tmpdir, input_code, expected_output):
        self.run_and_assert(tmpdir, input_code, expected_output)

    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """
                from pkg_resources import get_distribution
                dist = get_distribution("package_name")
                """,
                """
                from importlib.metadata import distribution

                dist = distribution("package_name")
                """,
            ),
            (
                """
                from pkg_resources import get_distribution
                version = get_distribution("package_name").version
                """,
                """
                from importlib.metadata import distribution

                version = distribution("package_name").version
                """,
            ),
        ],
    )
    def test_from_import(self, tmpdir, input_code, expected_output):
        self.run_and_assert(tmpdir, input_code, expected_output)

    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """
                from pkg_resources import get_distribution as get
                dist = get("package_name")
                """,
                """
                from importlib.metadata import distribution

                dist = distribution("package_name")
                """,
            ),
            (
                """
                from pkg_resources import get_distribution as get
                version = get("package_name").version
                """,
                """
                from importlib.metadata import distribution

                version = distribution("package_name").version
                """,
            ),
        ],
    )
    def test_import_alias(self, tmpdir, input_code, expected_output):
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_multiple(self, tmpdir):
        original_code = """
        import pkg_resources
        dist = pkg_resources.get_distribution("Django")
        dist.location
        version = dist.version
        """
        expected_output = """
        from importlib.metadata import distribution
        
        dist = distribution("Django")
        dist.location
        version = dist.version
        """
        self.run_and_assert(tmpdir, original_code, expected_output)
