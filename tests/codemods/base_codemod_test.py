# pylint: disable=no-member,not-callable,attribute-defined-outside-init
import argparse
from collections import defaultdict
import os
from pathlib import Path
from textwrap import dedent
from typing import ClassVar
import libcst as cst
from libcst.codemod import CodemodContext
import mock

from codemodder.context import CodemodExecutionContext
from codemodder.code_directory import DEFAULT_INCLUDED_PATHS, DEFAULT_EXCLUDED_PATHS
from codemodder.file_context import FileContext
from codemodder.registry import CodemodRegistry, CodemodCollection
from codemodder.semgrep import run as semgrep_run


class BaseCodemodTest:
    codemod: ClassVar = NotImplemented

    def setup_method(self):
        self.file_context = None

    def _make_context(self, root):
        cli_args = argparse.Namespace(
            directory=root,
            dry_run=True,
            verbose=False,
            path_include=DEFAULT_INCLUDED_PATHS,
            path_exclude=DEFAULT_EXCLUDED_PATHS,
        )
        return CodemodExecutionContext(cli_args, registry=mock.MagicMock())

    def run_and_assert(self, tmpdir, input_code, expected):
        tmp_file_path = tmpdir / "code.py"
        self.run_and_assert_filepath(tmpdir, tmp_file_path, input_code, expected)

    def run_and_assert_filepath(self, root, file_path, input_code, expected):
        input_tree = cst.parse_module(dedent(input_code))
        self.execution_context = self._make_context(root)
        self.file_context = FileContext(
            file_path,
            [],
            [],
            defaultdict(list),
        )
        wrapper = cst.MetadataWrapper(input_tree)
        command_instance = self.codemod(
            CodemodContext(wrapper=wrapper),
            self.execution_context,
            self.file_context,
        )
        output_tree = command_instance.transform_module(input_tree)

        assert output_tree.code == dedent(expected)

    def assert_dependency(self, dependency: str):
        assert self.file_context and self.file_context.dependencies == set([dependency])


class BaseSemgrepCodemodTest(BaseCodemodTest):
    @classmethod
    def setup_class(cls):
        collection = CodemodCollection(
            origin="pixee",
            codemods=[cls.codemod],
            docs_module="core_codemods.docs",
            semgrep_config_module="core_codemods.semgrep",
        )
        cls.registry = CodemodRegistry()
        cls.registry.add_codemod_collection(collection)

    def results_by_id_filepath(self, input_code, file_path):
        with open(file_path, "w", encoding="utf-8") as tmp_file:
            tmp_file.write(input_code)

        name = self.codemod.name()
        results = self.registry.match_codemods(codemod_include=[name])
        return semgrep_run(self.execution_context, results[0].yaml_files)

    def run_and_assert_filepath(self, root, file_path, input_code, expected):
        self.execution_context = self._make_context(root)
        input_tree = cst.parse_module(input_code)
        all_results = self.results_by_id_filepath(input_code, file_path)
        results = all_results[str(file_path)]
        self.file_context = FileContext(
            file_path,
            [],
            [],
            results,
        )
        wrapper = cst.MetadataWrapper(input_tree)
        command_instance = self.codemod(
            CodemodContext(wrapper=wrapper),
            self.execution_context,
            self.file_context,
        )
        output_tree = command_instance.transform_module(input_tree)

        assert output_tree.code == expected


class BaseDjangoCodemodTest(BaseSemgrepCodemodTest):
    def create_dir_structure(self, tmpdir):
        django_root = Path(tmpdir) / "mysite"
        settings_folder = django_root / "mysite"
        os.makedirs(settings_folder)
        return (django_root, settings_folder)
