from dependency_manager import DependencyManagerAbstract
from pathlib import Path
from codemodder import global_state


class DependencyManager(DependencyManagerAbstract):
    def get_parent_dir(self):
        return Path(global_state.DIRECTORY)
