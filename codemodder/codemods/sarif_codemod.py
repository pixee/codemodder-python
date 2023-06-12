from codemodder.codemods.base_codemod import BaseCodemod


class SarifCodemod(BaseCodemod):
    """
    A codemod that wants sarif results annotated with a list of RULE_ID
    RULE_ID: A set of sarif ids that whose results the codemod will act upon
    """

    RULE_IDS = set()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not cls.RULE_IDS:
            raise NotImplementedError("You forgot to define class attribute: RULE_IDS")
