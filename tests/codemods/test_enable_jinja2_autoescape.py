from core_codemods.enable_jinja2_autoescape import EnableJinja2Autoescape
from tests.codemods.base_codemod_test import BaseSemgrepCodemodTest


class TestEnableJinja2Autoescape(BaseSemgrepCodemodTest):
    codemod = EnableJinja2Autoescape

    def test_name(self):
        assert self.codemod.name() == "enable-jinja2-autoescape"

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
