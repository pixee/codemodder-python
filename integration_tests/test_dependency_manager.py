import os
import pathlib
import shutil
import subprocess
import tempfile
from textwrap import dedent

import pytest

from codemodder.codemods.test.integration_utils import SAMPLES_DIR


class TestDependencyManager:
    @classmethod
    def setup_class(cls):
        cls.output_path = tempfile.mkstemp()[1]
        cls.toml_file = "pyproject.toml"
        cls.requirements_file = "requirements.txt"
        cls.setup_file = "setup.py"

    @classmethod
    def teardown_class(cls):
        """Ensure any re-written file is undone after integration test class"""
        pathlib.Path(cls.output_path).unlink(missing_ok=True)

    @pytest.fixture
    def tmp_repo(self, tmp_path):
        (tmp_path / self.toml_file).touch()
        (tmp_path / self.requirements_file).touch()
        (tmp_path / self.setup_file).touch()
        with open(tmp_path / self.requirements_file, "w", encoding="utf-8") as req:
            req.write("requests")
        shutil.copy(SAMPLES_DIR + "/make_request.py", tmp_path)
        return tmp_path

    def write_pyproject_toml(self, tmp_repo):
        toml = dedent(
            """\
        [project]
        dependencies = [
        "requests",
        ]
        """
        )
        with open(tmp_repo / self.toml_file, "w", encoding="utf-8") as file:
            file.write(toml)

    def write_setup_file(self, tmp_repo):
        setup = dedent(
            """\
        from setuptools import setup, find_packages
        setup(
        name='test',
        version='3.0.0',
        packages=find_packages(where="."),
        install_requires=["requests"],
        )
        """
        )
        with open(tmp_repo / self.setup_file, "w", encoding="utf-8") as file:
            file.write(setup)

    def test_add_to_pyproject_toml(self, tmp_repo):
        self.write_pyproject_toml(tmp_repo)
        command = [
            "codemodder",
            tmp_repo,
            "--output",
            self.output_path,
            "--codemod-include=pixee:python/url-sandbox",
            "--verbose",
        ]
        completed_process = subprocess.run(
            command,
            check=False,
            shell=False,
            capture_output=True,
            encoding="utf-8",
        )
        lines = completed_process.stdout.splitlines()
        assert completed_process.returncode == 0
        assert (
            f"The following dependencies were added to '{tmp_repo / self.toml_file}': security"
            in lines
        )

    def test_add_to_requirements_txt(self, tmp_repo):
        command = [
            "codemodder",
            tmp_repo,
            "--output",
            self.output_path,
            "--codemod-include=pixee:python/url-sandbox",
            "--verbose",
        ]
        completed_process = subprocess.run(
            command,
            check=False,
            shell=False,
            capture_output=True,
            encoding="utf-8",
        )
        lines = completed_process.stdout.splitlines()
        assert completed_process.returncode == 0
        assert (
            f"The following dependencies were added to '{tmp_repo / self.requirements_file}': security"
            in lines
        )

    def test_add_to_setup(self, tmp_repo):
        os.chmod(tmp_repo / self.requirements_file, 0o400)
        self.write_setup_file(tmp_repo)
        command = [
            "codemodder",
            tmp_repo,
            "--output",
            self.output_path,
            "--codemod-include=pixee:python/url-sandbox",
            "--verbose",
        ]
        completed_process = subprocess.run(
            command,
            check=False,
            shell=False,
            capture_output=True,
            encoding="utf-8",
        )
        lines = completed_process.stdout.splitlines()
        assert completed_process.returncode == 0
        assert (
            f"The following dependencies were added to '{tmp_repo / self.setup_file}': security"
            in lines
        )

    def test_fail_to_add(self, tmp_repo):
        os.chmod(tmp_repo / self.requirements_file, 0o400)

        command = [
            "codemodder",
            tmp_repo,
            "--output",
            self.output_path,
            "--codemod-include=pixee:python/url-sandbox",
            "--verbose",
        ]
        completed_process = subprocess.run(
            command,
            check=False,
            shell=False,
            capture_output=True,
            encoding="utf-8",
        )
        lines = completed_process.stdout.splitlines()
        assert completed_process.returncode == 0
        assert "The following dependencies could not be added: security" in lines
