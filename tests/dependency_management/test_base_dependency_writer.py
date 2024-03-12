from codemodder.codetf import ChangeSet
from codemodder.dependency import Dependency, Requirement
from codemodder.dependency_management.base_dependency_writer import DependencyWriter
from codemodder.project_analysis.file_parsers.package_store import PackageStore


class FakeDependencyWriter(DependencyWriter):
    def add_to_file(
        self, dependencies: list[Dependency], dry_run: bool = False
    ) -> ChangeSet | None:
        del dependencies, dry_run
        return None


def test_add_dependency(mocker):
    mocker.patch("codemodder.dependency_management.base_dependency_writer.Path")

    dependency_store = PackageStore(mocker.Mock(), mocker.Mock(), set(), [])
    dep = FakeDependencyWriter(
        dependency_store=dependency_store,
        parent_directory=mocker.Mock(),
    )

    requirement = Requirement("foo==1.0.0")
    dependency = Dependency(
        requirement,
        mocker.Mock(),
        mocker.Mock(),
        mocker.Mock(),
        mocker.Mock(),
    )

    dep.add([dependency])
    assert dependency_store.dependencies == {dependency.requirement}


def test_add_dependency_already_exists(mocker):
    mocker.patch("codemodder.dependency_management.base_dependency_writer.Path")

    dependency_store = PackageStore(
        mocker.Mock(), mocker.Mock(), {Requirement("foo==1.0.0")}, []
    )
    dep = FakeDependencyWriter(
        dependency_store=dependency_store,
        parent_directory=mocker.Mock(),
    )

    requirement = Requirement("foo==1.0.0")
    dependency = Dependency(
        requirement,
        mocker.Mock(),
        mocker.Mock(),
        mocker.Mock(),
        mocker.Mock(),
    )

    dep.add([dependency])
    assert dependency_store.dependencies == {dependency.requirement}


def test_add_dependency_already_exists_different_version(mocker):
    mocker.patch("codemodder.dependency_management.base_dependency_writer.Path")

    original_requirement = Requirement("foo==1.0.0")
    dependency_store = PackageStore(
        mocker.Mock(), mocker.Mock(), {original_requirement}, []
    )
    dep = FakeDependencyWriter(
        dependency_store=dependency_store,
        parent_directory=mocker.Mock(),
    )

    requirement = Requirement("foo==2.0.0")
    dependency = Dependency(
        requirement,
        mocker.Mock(),
        mocker.Mock(),
        mocker.Mock(),
        mocker.Mock(),
    )

    dep.add([dependency])
    assert dependency_store.dependencies == {original_requirement}
