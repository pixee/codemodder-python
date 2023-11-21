from codemodder.dependency_management.setup_py_codemod import SetupPyAddDependencies
from libcst.codemod import CodemodTest, CodemodContext
from packaging.requirements import Requirement

TEST_DEPENDENCIES = [Requirement("defusedxml==0.7.1"), Requirement("security~=1.2.0")]


class TestSetupPyCodemod(CodemodTest):
    TRANSFORM = SetupPyAddDependencies
    CONTEXT = CodemodContext(filename="pkg/setup.py")

    def test_setup_call(self):
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
                "requests>=2.4.2,<3",
            ],
            entry_points={},
        )
        """

        after = ""

        self.assertCodemod(
            before, after, TEST_DEPENDENCIES, context_override=self.CONTEXT
        )

    # def test_different_setup_call(self):
    # test does not call install_requires
    # test with no dependencies inside install_requires
