from codemodder.dependency_management.base_dependency_writer import DependencyWriter


class RequirementsTxtWriter(DependencyWriter):
    def write(
        self, dependencies: list[Requirement], dry_run: bool = False
    ) -> Optional[ChangeSet]:
        pass
