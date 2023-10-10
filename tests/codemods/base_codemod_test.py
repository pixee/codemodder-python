# pylint: disable=no-member,not-callable,attribute-defined-outside-init
import libcst as cst
from libcst.codemod import CodemodContext
from pathlib import Path
import os
from collections import defaultdict
from codemodder.context import CodemodExecutionContext
from codemodder.file_context import FileContext
from codemodder.registry import CodemodRegistry, CodemodCollection
from codemodder.semgrep import run as semgrep_run
from typing import ClassVar

import mock


class BaseCodemodTest:
    codemod: ClassVar = NotImplemented

    def setup_method(self):
        self.file_context = None

    def run_and_assert(self, tmpdir, input_code, expected):
        tmp_file_path = tmpdir / "code.py"
        self.run_and_assert_filepath(tmpdir, tmp_file_path, input_code, expected)

    def run_and_assert_filepath(self, root, file_path, input_code, expected):
        input_tree = cst.parse_module(input_code)
        self.execution_context = CodemodExecutionContext(
            directory=root,
            dry_run=True,
            verbose=False,
            registry=mock.MagicMock(),
        )
        self.file_context = FileContext(
            file_path,
            [],
            [],
            defaultdict(list),
        )
        command_instance = self.codemod(
            CodemodContext(),
            self.execution_context,
            self.file_context,
        )
        output_tree = command_instance.transform_module(input_tree)

        assert output_tree.code == expected


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
        self.execution_context = CodemodExecutionContext(
            directory=root,
            dry_run=True,
            verbose=False,
            registry=mock.MagicMock(),
        )
        input_tree = cst.parse_module(input_code)
        all_results = self.results_by_id_filepath(input_code, file_path)
        results = all_results[str(file_path)]
        self.file_context = FileContext(
            file_path,
            [],
            [],
            results,
        )
        command_instance = self.codemod(
            CodemodContext(),
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
