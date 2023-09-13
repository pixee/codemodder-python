from dependency_manager import DependencyManagerAbstract
from pathlib import Path

from codemodder.context import CodemodExecutionContext


def write_dependencies(execution_context: CodemodExecutionContext):
    class DependencyManager(DependencyManagerAbstract):
        def get_parent_dir(self):
            return Path(execution_context.directory)

    dm = DependencyManager()
    dm.add(list(execution_context.dependencies))
    dm.write(dry_run=execution_context.dry_run)
    return dm
