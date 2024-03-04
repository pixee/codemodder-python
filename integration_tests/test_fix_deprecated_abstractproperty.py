from textwrap import dedent

from codemodder.codemods.test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)
from core_codemods.fix_deprecated_abstractproperty import FixDeprecatedAbstractproperty


class TestFixDeprecatedAbstractproperty(BaseIntegrationTest):
    codemod = FixDeprecatedAbstractproperty
    code_path = "tests/samples/deprecated_abstractproperty.py"

    original_code, _ = original_and_expected_from_code_path(code_path, [])
    expected_new_code = dedent(
        """\
    from abc import abstractmethod
    import abc


    class A:
        @property
        @abc.abstractmethod
        def foo(self):
            pass

        @classmethod
        @abc.abstractmethod
        def hello(cls):
            pass

        @staticmethod
        @abc.abstractmethod
        def goodbye():
            pass
                        
        @abstractmethod
        def bar(self):
            pass
    """
    )

    # fmt: off
    expected_diff =(
    """--- \n"""
    """+++ \n"""
    """@@ -1,16 +1,20 @@\n"""
    """-from abc import abstractproperty as ap, abstractclassmethod, abstractstaticmethod, abstractmethod\n"""
    """+from abc import abstractmethod\n"""
    """+import abc\n"""
    """ \n"""
    """ \n"""
    """ class A:\n"""
    """-    @ap\n"""
    """+    @property\n"""
    """+    @abc.abstractmethod\n"""
    """     def foo(self):\n"""
    """         pass\n"""
    """ \n"""
    """-    @abstractclassmethod\n"""
    """+    @classmethod\n"""
    """+    @abc.abstractmethod\n"""
    """     def hello(cls):\n"""
    """         pass\n"""
    """ \n"""
    """-    @abstractstaticmethod\n"""
    """+    @staticmethod\n"""
    """+    @abc.abstractmethod\n"""
    """     def goodbye():\n"""
    """         pass\n"""
    """ \n"""
    )
    # fmt: on
    expected_line_change = "5"
    num_changes = 3
    change_description = FixDeprecatedAbstractproperty.change_description
