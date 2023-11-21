import pytest
import libcst as cst
from codemodder.dependency_management.setup_py_codemod import SetupPyAddDependencies
from libcst.codemod import CodemodContext
from tests.codemods.base_codemod_test import BaseCodemodTest
from packaging.requirements import Requirement
from pathlib import Path

TEST_DEPENDENCIES = [Requirement("defusedxml==0.7.1"), Requirement("security~=1.2.0")]


class TestSetupPyCodemod(BaseCodemodTest):
    codemod = SetupPyAddDependencies

    def initialize_codemod(self, input_tree):
        """This codemod is initialized with different args than other codemods."""
        wrapper = cst.MetadataWrapper(input_tree)
        codemod_instance = self.codemod(
            CodemodContext(wrapper=wrapper),
            self.file_context,
            dependencies=TEST_DEPENDENCIES,
        )
        return codemod_instance

    def test_setup_call(self, tmpdir):
        before = """
        from setuptools import setup
        setup(
            name="test pkg",
            description="testing",
            long_description="...",
            author="Pixee",
            packages=find_packages("src"),
            package_dir={"": "src"},
            python_requires=">3.6",
            install_requires=[
                "protobuf>=3.12,<3.18; python_version < '3'",
                "protobuf>=3.12,<4; python_version >= '3'",
                "psutil>=5.7,<6",
                "requests>=2.4.2,<3"
            ],
            entry_points={},
        )
        """

        after = """
        from setuptools import setup
        setup(
            name="test pkg",
            description="testing",
            long_description="...",
            author="Pixee",
            packages=find_packages("src"),
            package_dir={"": "src"},
            python_requires=">3.6",
            install_requires=[
                "protobuf>=3.12,<3.18; python_version < '3'",
                "protobuf>=3.12,<4; python_version >= '3'",
                "psutil>=5.7,<6",
                "requests>=2.4.2,<3", "defusedxml==0.7.1", "security~=1.2.0"
            ],
            entry_points={},
        )
        """
        tmp_file_path = Path(tmpdir / "setup.py")
        self.run_and_assert_filepath(tmpdir, tmp_file_path, before, after)

    def test_other_setup_func(self, tmpdir):
        before = """
        from something import setup
        setup(
            name="test pkg",
            install_requires=[
                "protobuf>=3.12,<3.18; python_version < '3'",
                "protobuf>=3.12,<4; python_version >= '3'",
                "psutil>=5.7,<6",
                "requests>=2.4.2,<3"
            ],
            entry_points={},
        )
        """
        tmp_file_path = Path(tmpdir / "setup.py")
        self.run_and_assert_filepath(tmpdir, tmp_file_path, before, before)

    def test_not_setup_file(self, tmpdir):
        before = """
        from setuptools import setup
        setup(
            name="test pkg",
            description="testing",
            long_description="...",
            author="Pixee",
            packages=find_packages("src"),
            package_dir={"": "src"},
            python_requires=">3.6",
            install_requires=[
                "protobuf>=3.12,<3.18; python_version < '3'",
                "protobuf>=3.12,<4; python_version >= '3'",
                "psutil>=5.7,<6",
                "requests>=2.4.2,<3"
            ],
            entry_points={},
        )
        """
        tmp_file_path = Path(tmpdir / "not-setup.py")
        self.run_and_assert_filepath(tmpdir, tmp_file_path, before, before)

    def test_setup_call_no_install_requires(self, tmpdir):
        before = """
        from setuptools import setup
        setup(
            name="test pkg",
            description="testing",
            long_description="...",
            author="Pixee",
            packages=find_packages("src"),
            package_dir={"": "src"},
            python_requires=">3.6",
        )
        """
        tmp_file_path = Path(tmpdir / "setup.py")
        self.run_and_assert_filepath(tmpdir, tmp_file_path, before, before)

    def test_setup_no_existing_requirements(self, tmpdir):
        before = """
        from setuptools import setup
        setup(
            name="test pkg",
            description="testing",
            long_description="...",
            author="Pixee",
            packages=find_packages("src"),
            package_dir={"": "src"},
            python_requires=">3.6",
            install_requires=[],
            entry_points={},
        )
        """

        after = """
        from setuptools import setup
        setup(
            name="test pkg",
            description="testing",
            long_description="...",
            author="Pixee",
            packages=find_packages("src"),
            package_dir={"": "src"},
            python_requires=">3.6",
            install_requires=["defusedxml==0.7.1", "security~=1.2.0"],
            entry_points={},
        )
        """
        tmp_file_path = Path(tmpdir / "setup.py")
        self.run_and_assert_filepath(tmpdir, tmp_file_path, before, after)

    def test_setup_call_bad_install_requires(self, tmpdir):
        before = """
        from setuptools import setup
        setup(
            name="test pkg",
            description="testing",
            long_description="...",
            author="Pixee",
            packages=find_packages("src"),
            package_dir={"": "src"},
            python_requires=">3.6",
            install_requires="some-package",
        )
        """
        tmp_file_path = Path(tmpdir / "setup.py")
        self.run_and_assert_filepath(tmpdir, tmp_file_path, before, before)

    @pytest.mark.skip("Need to add support.")
    def test_setup_call_requirements_separate(self, tmpdir):
        before = """
        from setuptools import setup
        requirements = [
                "protobuf>=3.12,<3.18; python_version < '3'",
                "protobuf>=3.12,<4; python_version >= '3'",
                "psutil>=5.7,<6",
                "requests>=2.4.2,<3"
        ]
        setup(
            name="test pkg",
            description="testing",
            long_description="...",
            author="Pixee",
            packages=find_packages("src"),
            package_dir={"": "src"},
            python_requires=">3.6",
            install_requires=requirements,
            entry_points={},
        )
        """

        after = """
        from setuptools import setup
        requirements = [
                "protobuf>=3.12,<3.18; python_version < '3'",
                "protobuf>=3.12,<4; python_version >= '3'",
                "psutil>=5.7,<6",
                "requests>=2.4.2,<3", "defusedxml==0.7.1", "security~=1.2.0"
        ]
        setup(
            name="test pkg",
            description="testing",
            long_description="...",
            author="Pixee",
            packages=find_packages("src"),
            package_dir={"": "src"},
            python_requires=">3.6",
            install_requires=requirements,
            entry_points={},
        )
        """
        tmp_file_path = Path(tmpdir / "setup.py")
        self.run_and_assert_filepath(tmpdir, tmp_file_path, before, after)
