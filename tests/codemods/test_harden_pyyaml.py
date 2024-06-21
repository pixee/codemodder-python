import pytest
import yaml

from codemodder.codemods.test import BaseCodemodTest
from core_codemods.harden_pyyaml import HardenPyyaml

UNSAFE_LOADERS = yaml.loader.__all__.copy()  # type: ignore
UNSAFE_LOADERS.remove("SafeLoader")
loaders = pytest.mark.parametrize("loader", UNSAFE_LOADERS)


class TestHardenPyyaml(BaseCodemodTest):
    codemod = HardenPyyaml

    def test_name(self):
        assert self.codemod.name == "harden-pyyaml"

    def test_safe_loader(self, tmpdir):
        input_code = """import yaml
data = b'!!python/object/apply:subprocess.Popen \\n- ls'
deserialized_data = yaml.load(data, Loader=yaml.SafeLoader)
"""
        self.run_and_assert(tmpdir, input_code, input_code)

    @loaders
    def test_all_unsafe_loaders_arg(self, tmpdir, loader):
        input_code = f"""import yaml
data = b'!!python/object/apply:subprocess.Popen \\n- ls'
deserialized_data = yaml.load(data, yaml.{loader})
"""

        expected = """import yaml
data = b'!!python/object/apply:subprocess.Popen \\n- ls'
deserialized_data = yaml.load(data, yaml.SafeLoader)
"""
        self.run_and_assert(tmpdir, input_code, expected)

    @loaders
    def test_all_unsafe_loaders_kwarg(self, tmpdir, loader):
        input_code = f"""import yaml
data = b'!!python/object/apply:subprocess.Popen \\n- ls'
deserialized_data = yaml.load(data, Loader=yaml.{loader})
"""

        expected = """import yaml
data = b'!!python/object/apply:subprocess.Popen \\n- ls'
deserialized_data = yaml.load(data, Loader=yaml.SafeLoader)
"""
        self.run_and_assert(tmpdir, input_code, expected)

    def test_import_alias(self, tmpdir):
        input_code = """import yaml as yam
from yaml import Loader

data = b'!!python/object/apply:subprocess.Popen \\n- ls'
deserialized_data = yam.load(data, Loader=Loader)
"""
        expected = """import yaml as yam
from yaml import Loader

data = b'!!python/object/apply:subprocess.Popen \\n- ls'
deserialized_data = yam.load(data, Loader=yam.SafeLoader)
"""
        self.run_and_assert(tmpdir, input_code, expected)

    def test_import_alias_add(self, tmpdir):
        input_code = """
data = b'!!python/object/apply:subprocess.Popen \\n- ls'
import yaml as yam
deserialized_data = yam.load(data)
"""
        expected = """
data = b'!!python/object/apply:subprocess.Popen \\n- ls'
import yaml as yam
deserialized_data = yam.load(data, Loader=yam.SafeLoader)
"""
        self.run_and_assert(tmpdir, input_code, expected)

    def test_preserve_custom_loader(self, tmpdir):
        expected = (
            input_code
        ) = """
        import yaml
        from custom import CustomLoader

        yaml.load(data, CustomLoader)
        """

        self.run_and_assert(tmpdir, input_code, expected)

    def test_preserve_custom_loader_kwarg(self, tmpdir):
        expected = (
            input_code
        ) = """
        import yaml
        from custom import CustomLoader

        yaml.load(data, Loader=CustomLoader)
        """

        self.run_and_assert(tmpdir, input_code, expected)

    def test_default_loader_unsafe(self, tmpdir):
        input_code = """
        import yaml

        yaml.load(data)
        """
        expected = """
        import yaml

        yaml.load(data, Loader=yaml.SafeLoader)
        """
        self.run_and_assert(tmpdir, input_code, expected)


class TestHardenPyyamlClassInherit(BaseCodemodTest):
    codemod = HardenPyyaml

    def test_safe_loader(self, tmpdir):
        input_code = """
        import yaml

        class MyCustomLoader(yaml.SafeLoader):
            def __init__(self, *args, **kwargs):
                super(MyCustomLoader, self).__init__(*args, **kwargs)

        """

        self.run_and_assert(tmpdir, input_code, input_code)

    @loaders
    def test_unsafe_loaders(self, tmpdir, loader):
        input_code = f"""
        import yaml

        class MyCustomLoader(yaml.{loader}):
            def __init__(self, *args, **kwargs):
                super(MyCustomLoader, self).__init__(*args, **kwargs)
        """
        expected = """
        import yaml

        class MyCustomLoader(yaml.SafeLoader):
            def __init__(self, *args, **kwargs):
                super(MyCustomLoader, self).__init__(*args, **kwargs)
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_from_import(self, tmpdir):
        input_code = """
        from yaml import UnsafeLoader

        class MyCustomLoader(UnsafeLoader):
            def __init__(self, *args, **kwargs):
                super(MyCustomLoader, self).__init__(*args, **kwargs)
        """
        expected = """
        from yaml import SafeLoader

        class MyCustomLoader(SafeLoader):
            def __init__(self, *args, **kwargs):
                super(MyCustomLoader, self).__init__(*args, **kwargs)
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_import_alias(self, tmpdir):
        input_code = """
        import yaml as yam

        class MyCustomLoader(yam.UnsafeLoader):
            def __init__(self, *args, **kwargs):
                super(MyCustomLoader, self).__init__(*args, **kwargs)
        """
        expected = """
        import yaml as yam

        class MyCustomLoader(yam.SafeLoader):
            def __init__(self, *args, **kwargs):
                super(MyCustomLoader, self).__init__(*args, **kwargs)
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_multiple_bases(self, tmpdir):
        input_code = """
        from abc import ABC
        import yaml as yam
        from whatever import Loader

        class MyCustomLoader(ABC, yam.UnsafeLoader, Loader):
            def __init__(self, *args, **kwargs):
                super(MyCustomLoader, self).__init__(*args, **kwargs)
        """
        expected = """
        from abc import ABC
        import yaml as yam
        from whatever import Loader

        class MyCustomLoader(ABC, yam.SafeLoader, Loader):
            def __init__(self, *args, **kwargs):
                super(MyCustomLoader, self).__init__(*args, **kwargs)
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_different_yaml(self, tmpdir):
        input_code = """
        from yaml import UnsafeLoader
        import whatever as yaml

        class MyLoader(UnsafeLoader, yaml.Loader):
            ...
        """
        expected = """
        from yaml import SafeLoader
        import whatever as yaml

        class MyLoader(SafeLoader, yaml.Loader):
            ...
        """
        self.run_and_assert(tmpdir, input_code, expected)
