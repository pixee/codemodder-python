from codemodder.codemods.test import BaseDjangoCodemodTest
from core_codemods.django_debug_flag_on import DjangoDebugFlagOn


class TestDjangoDebugFlagOn(BaseDjangoCodemodTest):
    codemod = DjangoDebugFlagOn

    def test_name(self):
        assert self.codemod.name == "django-debug-flag-on"

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
