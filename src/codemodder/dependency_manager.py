import sys
import io

from dependency_manager import DependencyManagerAbstract
from pathlib import Path

from codemodder.context import CodemodExecutionContext


def write_dependencies(execution_context: CodemodExecutionContext):
    class DependencyManager(DependencyManagerAbstract):
        def get_parent_dir(self):
            return Path(execution_context.directory)

    dm = DependencyManager()
    dm.add(list(execution_context.dependencies))

    try:
        # Hacky solution to prevent the dependency manager from writing to stdout
        sys.stdout = io.StringIO()
        dm.write(dry_run=execution_context.dry_run)
    finally:
        sys.stdout = sys.__stdout__

    return dm
