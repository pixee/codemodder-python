from typing import Mapping

from codemodder.codemods.import_modifier_codemod import ImportModifierCodemod
from codemodder.dependency import Dependency, Fickling
from core_codemods.api import Metadata, Reference, ReviewGuidance, SimpleCodemod


class HardenPickleLoad(SimpleCodemod, ImportModifierCodemod):
    metadata = Metadata(
        name="harden-pickle-load",
        summary="Harden `pickle.load()` against deserialization attacks",
        review_guidance=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
        references=[
            Reference(url="https://docs.python.org/3/library/pickle.html"),
            Reference(
                url="https://owasp.org/www-community/vulnerabilities/Deserialization_of_untrusted_data"
            ),
            Reference(
                url="https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html#clear-box-review_1"
            ),
            Reference(
                url="https://github.com/trailofbits/fickling",
            ),
        ],
    )

    change_description = "Harden `pickle.load()` against deserialization attacks"

    @property
    def dependency(self) -> Dependency:
        return Fickling

    @property
    def mapping(self) -> Mapping[str, str]:
        # NOTE: the fickling api doesn't seem to support `loads` yet
        return {
            "pickle.load": "fickling",
        }
