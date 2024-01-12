# pylint: disable=no-member,not-callable,attribute-defined-outside-init
import os
from pathlib import Path
from textwrap import dedent
from typing import ClassVar

import libcst as cst
from libcst.codemod import CodemodContext
import mock

from codemodder.context import CodemodExecutionContext
from codemodder.dependency import Dependency
from codemodder.file_context import FileContext
from codemodder.registry import CodemodRegistry, CodemodCollection
from codemodder.semgrep import run as semgrep_run


class BaseCodemodTest:
    codemod: ClassVar = NotImplemented

    def setup_method(self):
        self.file_context = None

    def initialize_codemod(self, input_tree):
        wrapper = cst.MetadataWrapper(input_tree)
        codemod_instance = self.codemod(
            CodemodContext(wrapper=wrapper),
            self.file_context,
        )
        return codemod_instance

    def run_and_assert(self, tmpdir, input_code, expected):
        tmp_file_path = Path(tmpdir / "code.py")
        self.run_and_assert_filepath(tmpdir, tmp_file_path, input_code, expected)

    def assert_no_change_line_excluded(
        self, tmpdir, input_code, expected, lines_to_exclude
    ):
        tmp_file_path = Path(tmpdir / "code.py")
        input_tree = cst.parse_module(dedent(input_code))
        self.execution_context = CodemodExecutionContext(
            directory=tmpdir,
            dry_run=True,
            verbose=False,
            registry=mock.MagicMock(),
            repo_manager=mock.MagicMock(),
        )

        self.file_context = FileContext(
            tmpdir,
            tmp_file_path,
            lines_to_exclude,
            [],
            [],
        )
        codemod_instance = self.initialize_codemod(input_tree)
        output_tree = codemod_instance.transform_module(input_tree)

        assert output_tree.code == dedent(expected)
        assert len(self.file_context.codemod_changes) == 0

    def run_and_assert_filepath(self, root, file_path, input_code, expected):
        input_tree = cst.parse_module(dedent(input_code))
        self.execution_context = CodemodExecutionContext(
            directory=root,
            dry_run=True,
            verbose=False,
            registry=mock.MagicMock(),
            repo_manager=mock.MagicMock(),
        )
        self.file_context = FileContext(
            root,
            file_path,
            [],
            [],
            [],
        )
        codemod_instance = self.initialize_codemod(input_tree)
        output_tree = codemod_instance.transform_module(input_tree)

        assert output_tree.code == dedent(expected)

    def assert_dependency(self, dependency: Dependency):
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
            tmp_file.write(dedent(input_code))

        name = self.codemod.name()
        results = self.registry.match_codemods(codemod_include=[name])
        return semgrep_run(self.execution_context, results[0].yaml_files)

    def run_and_assert_filepath(self, root, file_path, input_code, expected):
        self.execution_context = CodemodExecutionContext(
            directory=root,
            dry_run=True,
            verbose=False,
            registry=mock.MagicMock(),
            repo_manager=mock.MagicMock(),
        )
        input_tree = cst.parse_module(dedent(input_code))
        all_results = self.results_by_id_filepath(input_code, file_path)
        results = all_results.results_for_rule_and_file(self.codemod.name(), file_path)
        self.file_context = FileContext(
            root,
            file_path,
            [],
            [],
            results,
        )
        codemod_instance = self.initialize_codemod(input_tree)
        output_tree = codemod_instance.transform_module(input_tree)

        assert output_tree.code == dedent(expected)


class BaseDjangoCodemodTest(BaseSemgrepCodemodTest):
    def create_dir_structure(self, tmpdir):
        django_root = Path(tmpdir) / "mysite"
        settings_folder = django_root / "mysite"
        os.makedirs(settings_folder)
        return (django_root, settings_folder)
