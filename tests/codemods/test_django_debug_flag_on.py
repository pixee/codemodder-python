from pathlib import Path
from codemodder.codemods.django_debug_flag_on import DjangoDebugFlagOn
import os

from tests.codemods.base_codemod_test import BaseCodemodTest


class TestDjangoDebugFlagOn(BaseCodemodTest):
    codemod = DjangoDebugFlagOn

    def test_rule_ids(self):
        assert self.codemod.RULE_IDS == ["django-debug-flag-on"]

    def create_dir_structure(self, tmpdir):
        django_root = Path(tmpdir) / "mysite"
        settings_folder = django_root / "mysite"
        os.makedirs(settings_folder)
        return (django_root, settings_folder)

    def test_settings_dot_py(self, tmpdir):
        django_root, settings_folder = self.create_dir_structure(tmpdir)
        (django_root / "manage.py").touch()
        file_path = settings_folder / "settings.py"
        input_code = """DEBUG = True"""
        expected = """DEBUG = False"""
        self.run_and_assert_filepath(django_root, file_path, input_code, expected)

    def test_not_settings_dot_py(self, tmpdir):
        django_root, settings_folder = self.create_dir_structure(tmpdir)
        (django_root / "manage.py").touch()
        file_path = settings_folder / "code.py"
        input_code = """DEBUG = True"""
        expected = input_code
        self.run_and_assert_filepath(django_root, file_path, input_code, expected)

    def test_no_manage_dot_py(self, tmpdir):
        django_root, settings_folder = self.create_dir_structure(tmpdir)
        file_path = settings_folder / "settings.py"
        input_code = """DEBUG = True"""
        expected = input_code
        self.run_and_assert_filepath(django_root, file_path, input_code, expected)
