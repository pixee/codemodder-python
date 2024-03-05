import pytest

from codemodder.codemods.test import BaseDjangoCodemodTest
from core_codemods.django_session_cookie_secure_off import DjangoSessionCookieSecureOff


class TestDjangoSessionSecureCookieOff(BaseDjangoCodemodTest):
    codemod = DjangoSessionCookieSecureOff

    def test_name(self):
        assert self.codemod.name == "django-session-cookie-secure-off"

    def test_not_settings_dot_py(self, tmpdir):
        django_root, settings_folder = self.create_dir_structure(tmpdir)
        (django_root / "manage.py").touch()
        file_path = settings_folder / "code.py"
        input_code = """SESSION_COOKIE_SECURE = True"""
        expected = input_code
        self.run_and_assert_filepath(django_root, file_path, input_code, expected)

    def test_no_manage_dot_py(self, tmpdir):
        django_root, settings_folder = self.create_dir_structure(tmpdir)
        file_path = settings_folder / "settings.py"
        input_code = """SESSION_COOKIE_SECURE = True"""
        expected = input_code
        self.run_and_assert_filepath(django_root, file_path, input_code, expected)

    def test_settings_dot_py_secure_true(self, tmpdir):
        django_root, settings_folder = self.create_dir_structure(tmpdir)
        (django_root / "manage.py").touch()
        file_path = settings_folder / "settings.py"
        input_code = """DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SESSION_COOKIE_SECURE = True
"""
        self.run_and_assert_filepath(django_root, file_path, input_code, input_code)

    @pytest.mark.parametrize("value", ["False", "gibberish"])
    def test_settings_dot_py_secure_bad(self, tmpdir, value):
        django_root, settings_folder = self.create_dir_structure(tmpdir)
        (django_root / "manage.py").touch()
        file_path = settings_folder / "settings.py"
        input_code = f"""DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SESSION_COOKIE_SECURE = {value}
"""
        expected = """DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SESSION_COOKIE_SECURE = True
"""
        self.run_and_assert_filepath(django_root, file_path, input_code, expected)

    def test_settings_dot_py_secure_missing(self, tmpdir):
        django_root, settings_folder = self.create_dir_structure(tmpdir)
        (django_root / "manage.py").touch()
        file_path = settings_folder / "settings.py"
        input_code = """DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
"""
        expected = """DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SESSION_COOKIE_SECURE = True
"""
        self.run_and_assert_filepath(django_root, file_path, input_code, expected)
