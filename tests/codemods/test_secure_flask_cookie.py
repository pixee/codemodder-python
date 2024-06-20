import pytest

from codemodder.codemods.test import BaseCodemodTest
from core_codemods.secure_flask_cookie import SecureFlaskCookie

each_func = pytest.mark.parametrize("func", ["make_response", "Response"])


class TestSecureFlaskCookie(BaseCodemodTest):
    codemod = SecureFlaskCookie

    def test_name(self):
        assert self.codemod.name == "secure-flask-cookie"

    @each_func
    def test_import(self, tmpdir, func):
        input_code = f"""
        import flask

        response = flask.{func}()
        var = "hello"
        response.set_cookie("name", "value")
        """
        expexted_output = f"""
        import flask

        response = flask.{func}()
        var = "hello"
        response.set_cookie("name", "value", secure=True, httponly=True, samesite='Lax')
        """
        self.run_and_assert(tmpdir, input_code, expexted_output)

    @each_func
    def test_from_import(self, tmpdir, func):
        input_code = f"""
        from flask import {func}

        response = {func}()
        var = "hello"
        response.set_cookie("name", "value")
        """
        expexted_output = f"""
        from flask import {func}

        response = {func}()
        var = "hello"
        response.set_cookie("name", "value", secure=True, httponly=True, samesite='Lax')
        """
        self.run_and_assert(tmpdir, input_code, expexted_output)

    @each_func
    def test_import_alias(self, tmpdir, func):
        input_code = f"""
        from flask import {func} as flask_resp
        var = "hello"
        flask_resp().set_cookie("name", "value")
        """
        expexted_output = f"""
        from flask import {func} as flask_resp
        var = "hello"
        flask_resp().set_cookie("name", "value", secure=True, httponly=True, samesite='Lax')
        """
        self.run_and_assert(tmpdir, input_code, expexted_output)

    @pytest.mark.parametrize(
        "input_args,expected_args",
        [
            (
                "secure=True",
                "secure=True, httponly=True, samesite='Lax'",
            ),
            (
                "secure=True, httponly=True, samesite='Lax'",
                "secure=True, httponly=True, samesite='Lax'",
            ),
            (
                "secure=True, httponly=True, samesite='Strict'",
                "secure=True, httponly=True, samesite='Strict'",
            ),
            (
                "secure=False, httponly=True, samesite='Strict'",
                "secure=True, httponly=True, samesite='Strict'",
            ),
            (
                "httponly=True, samesite='Lax', secure=True",
                "httponly=True, samesite='Lax', secure=True",
            ),
            (
                "secure=True, httponly=True",
                "secure=True, httponly=True, samesite='Lax'",
            ),
            (
                "secure=True, httponly=True, samesite=None",
                "secure=True, httponly=True, samesite='Lax'",
            ),
        ],
    )
    @each_func
    def test_verify_variations(self, tmpdir, func, input_args, expected_args):
        input_code = f"""
        import flask

        response = flask.{func}()
        var = "hello"
        response.set_cookie("name", "value", {input_args})
        """
        expexted_output = f"""
        import flask

        response = flask.{func}()
        var = "hello"
        response.set_cookie("name", "value", {expected_args})
        """
        self.run_and_assert(tmpdir, input_code, expexted_output)
