from functools import cache

from codemodder.codemods.base_detector import BaseDetector
from codemodder.codeql import CodeQLResultSet
from codemodder.context import CodemodExecutionContext
from codemodder.result import ResultSet


class CodeQLSarifFileDetector(BaseDetector):
    def apply(
        self,
        codemod_id: str,
        context: CodemodExecutionContext,
    ) -> ResultSet:
        del codemod_id
        return process_codeql_findings(
            tuple(context.tool_result_files_map.get("codeql", ()))
        )  # Convert list to tuple for cache hashability


@cache
def process_codeql_findings(codeql_sarif_files: tuple[str]) -> ResultSet:
    results = CodeQLResultSet()
    for file in codeql_sarif_files or ():
        results |= CodeQLResultSet.from_sarif(file)
    return results
