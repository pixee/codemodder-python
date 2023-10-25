import pytest
from core_codemods.secure_flask_cookie import SecureFlaskCookie
from tests.codemods.base_codemod_test import BaseSemgrepCodemodTest
from textwrap import dedent

each_func = pytest.mark.parametrize("func", ["make_response", "Response"])


class TestSecureFlaskCookie(BaseSemgrepCodemodTest):
    codemod = SecureFlaskCookie

    def test_name(self):
        assert self.codemod.name() == "secure-flask-cookie"

    @each_func
    def test_import(self, tmpdir, func):
        input_code = f"""\
        import flask

        response = flask.{func}()
        var = "hello"
        response.set_cookie("name", "value")
        """
        expexted_output = f"""\
        import flask

        response = flask.{func}()
        var = "hello"
        response.set_cookie("name", "value", secure=True, httponly=True, samesite='Lax')
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expexted_output))


#     @each_func
#     def test_from_import(self, tmpdir, func):
#         input_code = f"""from lxml.etree import {func}
#
# parser = {func}()
# var = "hello"
# """
#         expexted_output = f"""from lxml.etree import {func}
#
# parser = {func}(resolve_entities=False)
# var = "hello"
# """
#
#         self.run_and_assert(tmpdir, input_code, expexted_output)
#
#     @each_func
#     def test_from_import_module(self, tmpdir, func):
#         input_code = f"""from lxml import etree
#
# parser = etree.{func}()
# var = "hello"
# """
#         expexted_output = f"""from lxml import etree
#
# parser = etree.{func}(resolve_entities=False)
# var = "hello"
# """
#
#         self.run_and_assert(tmpdir, input_code, expexted_output)
#
#     @each_func
#     def test_import_alias(self, tmpdir, func):
#         input_code = f"""from lxml.etree import {func} as xmlfunc
#
# parser = xmlfunc()
# var = "hello"
# """
#         expexted_output = f"""from lxml.etree import {func} as xmlfunc
#
# parser = xmlfunc(resolve_entities=False)
# var = "hello"
# """
#
#         self.run_and_assert(tmpdir, input_code, expexted_output)
#
#     @pytest.mark.parametrize(
#         "input_args,expected_args",
#         [
#             (
#                 "resolve_entities=True",
#                 "resolve_entities=False",
#             ),
#             (
#                 "resolve_entities=False",
#                 "resolve_entities=False",
#             ),
#             (
#                 """resolve_entities=True, no_network=False, dtd_validation=True""",
#                 """resolve_entities=False, no_network=True, dtd_validation=False""",
#             ),
#             (
#                 """dtd_validation=True""",
#                 """dtd_validation=False, resolve_entities=False""",
#             ),
#             (
#                 """no_network=False""",
#                 """no_network=True, resolve_entities=False""",
#             ),
#             (
#                 """no_network=True""",
#                 """no_network=True, resolve_entities=False""",
#             ),
#         ],
#     )
#     @each_func
#     def test_verify_variations(self, tmpdir, func, input_args, expected_args):
#         input_code = f"""import lxml.etree
# parser = lxml.etree.{func}({input_args})
# var = "hello"
# """
#         expexted_output = f"""import lxml.etree
# parser = lxml.etree.{func}({expected_args})
# var = "hello"
# """
#         self.run_and_assert(tmpdir, input_code, expexted_output)
