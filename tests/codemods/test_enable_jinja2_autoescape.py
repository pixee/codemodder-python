import pytest

from codemodder.codemods.test import BaseCodemodTest
from core_codemods.enable_jinja2_autoescape import EnableJinja2Autoescape


class TestEnableJinja2Autoescape(BaseCodemodTest):
    codemod = EnableJinja2Autoescape

    def test_name(self):
        assert self.codemod.name == "enable-jinja2-autoescape"

    def test_import(self, tmpdir):
        input_code = """
        import jinja2
        env = jinja2.Environment()
        var = "hello"
        """
        expexted_output = """
        import jinja2
        env = jinja2.Environment(autoescape=True)
        var = "hello"
        """

        self.run_and_assert(tmpdir, input_code, expexted_output)

    def test_import_with_arg(self, tmpdir):
        input_code = """
        import jinja2
        env = jinja2.Environment(autoescape=False)
        var = "hello"
        """
        expexted_output = """
        import jinja2
        env = jinja2.Environment(autoescape=True)
        var = "hello"
        """

        self.run_and_assert(tmpdir, input_code, expexted_output)

    def test_import_with_more_args(self, tmpdir):
        input_code = """
        import jinja2
        env = jinja2.Environment(loader=some_loader, autoescape=False)
        var = "hello"
        """
        expexted_output = """
        import jinja2
        env = jinja2.Environment(loader=some_loader, autoescape=True)
        var = "hello"
        """

        self.run_and_assert(tmpdir, input_code, expexted_output)

    def test_import_with_other_args(self, tmpdir):
        input_code = """
        import jinja2
        env = jinja2.Environment(loader=some_loader)
        var = "hello"
        """
        expexted_output = """
        import jinja2
        env = jinja2.Environment(loader=some_loader, autoescape=True)
        var = "hello"
        """

        self.run_and_assert(tmpdir, input_code, expexted_output)

    def test_from_import(self, tmpdir):
        input_code = """
        from jinja2 import Environment
        env = Environment()
        var = "hello"
        """
        expexted_output = """
        from jinja2 import Environment
        env = Environment(autoescape=True)
        var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, expexted_output)

    def test_import_alias(self, tmpdir):
        input_code = """
        import jinja2 as templating
        env = templating.Environment()
        var = "hello"
        """
        expexted_output = """
        import jinja2 as templating
        env = templating.Environment(autoescape=True)
        var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, expexted_output)

    def test_autoescape_enabled(self, tmpdir):
        input_code = """
        import jinja2
        env = jinja2.Environment(autoescape=True)
        var = "hello"
        """
        expexted_output = input_code
        self.run_and_assert(tmpdir, input_code, expexted_output)

    @pytest.mark.parametrize(
        "code",
        [
            """
        import jinja2
        env = jinja2.Environment(autoescape=jinja2.select_autoescape())
        """,
            """
        import jinja2
        env = jinja2.Environment(autoescape=jinja2.select_autoescape(disabled_extensions=('txt',), default_for_string=True, default=True))
        """,
        ],
    )
    def test_autoescape_callable(self, tmpdir, code):
        self.run_and_assert(tmpdir, code, code)

    def test_kwargs_unpacked(self, tmpdir):
        input_code = (
            expexted_output
        ) = """
        import jinja2
        env = jinja2.Environment(**kwargs)
        var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, expexted_output)

    def test_kwargs_unpacked_with_autoescape(self, tmpdir):
        input_code = """
        import jinja2
        env = jinja2.Environment(**kwargs, autoescape=False)
        var = "hello"
        """
        expexted_output = """
        import jinja2
        env = jinja2.Environment(**kwargs, autoescape=True)
        var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, expexted_output)

    def test_kwargs_unpacked_with_autoescape_before(self, tmpdir):
        input_code = """
        import jinja2
        env = jinja2.Environment(autoescape=False, **kwargs)
        var = "hello"
        """
        expexted_output = """
        import jinja2
        env = jinja2.Environment(autoescape=True, **kwargs)
        var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, expexted_output)

    def test_aiohttp_import_setup(self, tmpdir):
        input_code = """
        import aiohttp_jinja2
        aiohttp_jinja2.setup(app, autoescape=False)
        """
        expected_output = """
        import aiohttp_jinja2
        aiohttp_jinja2.setup(app, autoescape=True)
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_aiohttp_import_from_setup(self, tmpdir):
        input_code = """
        from aiohttp_jinja2 import setup
        setup(app, autoescape=False)
        """
        expected_output = """
        from aiohttp_jinja2 import setup
        setup(app, autoescape=True)
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_aiohttp_import_alias(self, tmpdir):
        input_code = """
        from aiohttp_jinja2 import setup as setup_jinja2
        setup_jinja2(app, autoescape=False)
        """
        expected_output = """
        from aiohttp_jinja2 import setup as setup_jinja2
        setup_jinja2(app, autoescape=True)
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_aiohttp_import_alias_no_change(self, tmpdir):
        expected_output = (
            input_code
        ) = """
        from aiohttp_jinja2 import foo as setup
        setup_jinja2(app)
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_aiohttp_autoescape_default(self, tmpdir):
        input_code = """
        import aiohttp_jinja2
        aiohttp_jinja2.setup(app)
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_aiohttp_autoescape_True(self, tmpdir):
        input_code = """
        import aiohttp_jinja2
        aiohttp_jinja2.setup(app, autoescape=True)
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_aiohttp_autoescape_callable(self, tmpdir):
        input_code = """
        import aiohttp_jinja2
        import jinja
        aiohttp_jinja2.setup(app, autoescape=jinja2.select_autoescape())
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_aiohttp_autoescape_kwargs(self, tmpdir):
        input_code = """
        import aiohttp_jinja2
        aiohttp_jinja2.setup(app, **kwargs)
        """
        self.run_and_assert(tmpdir, input_code, input_code)
