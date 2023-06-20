from libcst.codemod import VisitorBasedCodemodCommand
from libcst.metadata import PositionProvider


class BaseVisitor(VisitorBasedCodemodCommand):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, context, results):
        super().__init__(context)
        self.results = results

    def filter_by_result(self, node):
        pos_to_match = self.get_metadata(PositionProvider, node)
        all_pos = [extract_pos_from_result(result) for result in self.results]
        return any(match_pos(pos_to_match, position) for position in all_pos)


def extract_pos_from_result(result):
    region = result["locations"][0]["physicalLocation"]["region"]
    # TODO it may be the case some of these attributes do not exist
    return (
        region.get("startLine"),
        region["startColumn"],
        region.get("endLine") or region.get("startLine"),
        region["endColumn"],
    )


def match_pos(pos, x):
    # needs some leeway because the semgrep and libcst won't exactly match
    return (
        pos.start.line == x[0]
        and (pos.start.column in (x[1] - 1, x[1]))
        and pos.end.line == x[2]
        and (pos.end.column in (x[3] - 1, x[3]))
    )
