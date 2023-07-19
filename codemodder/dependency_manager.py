from dependency_manager import DependencyManagerAbstract
from codemodder import global_state


class DependencyManager(DependencyManagerAbstract):
    def get_parent_dir(self):
        return global_state.DIRECTORY
