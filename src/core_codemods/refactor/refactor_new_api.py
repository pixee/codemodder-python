import libcst as cst

from codemodder.codemods.utils_mixin import NameResolutionMixin
from core_codemods.api import Metadata, ReviewGuidance, SimpleCodemod


class RefactorNewApi(SimpleCodemod, NameResolutionMixin):
    metadata = Metadata(
        name="refactor-new-api",
        summary="Refactor to use thew new simplified API",
        review_guidance=ReviewGuidance.MERGE_AFTER_REVIEW,
        description="",
    )

    new_api_module = "codemodder.codemods.new_api"
    new_api_class = "SimpleCodemod"

    no_whitespace_assign = cst.AssignEqual(
        whitespace_before=cst.SimpleWhitespace(""),
        whitespace_after=cst.SimpleWhitespace(""),
    )

    def _build_metadata(self, metadata: dict) -> tuple[cst.SimpleStatementLine, bool]:
        refs = (
            build_references(metadata["references"])
            if "references" in metadata
            else cst.List(elements=[])
        )

        return (
            cst.SimpleStatementLine(
                body=[
                    cst.Assign(
                        targets=[cst.AssignTarget(target=cst.Name(value="metadata"))],
                        value=cst.Call(
                            func=cst.Name(value="Metadata"),
                            args=[
                                make_metadata_arg(metadata, "name"),
                                make_metadata_arg(metadata, "summary"),
                                make_metadata_arg(metadata, "review_guidance"),
                                make_metadata_arg(
                                    metadata, "references", value=refs, last=True
                                ),
                            ],
                            whitespace_before_args=cst.ParenthesizedWhitespace(
                                indent=True,
                                last_line=cst.SimpleWhitespace("    "),
                            ),
                        ),
                    )
                ]
            ),
            bool(refs.elements),
        )

    def find_metadata(
        self, assign: cst.Assign
    ) -> tuple[str, cst.BaseExpression] | None:
        match assign:
            case cst.Assign(
                targets=[cst.AssignTarget(target=cst.Name(value=name))],
                value=value,
            ):
                match name:
                    case "NAME" as name:
                        return name, value
                    case "SUMMARY" as name:
                        return name, value
                    case "DESCRIPTION" as name:
                        return name, value
                    case "REVIEW_GUIDANCE" as name:
                        return name, value
                    case "REFERENCES" as name:
                        return name, value
                    case "CHANGE_DESCRIPTION" | "change_description" as name:
                        return name, value

        return None

    def create_rule(self, body: cst.BaseSuite) -> cst.SimpleStatementLine:
        match body:
            case cst.IndentedBlock(
                body=[
                    cst.SimpleStatementLine(
                        body=[cst.Return(value=cst.SimpleString() as value)]
                    )
                ]
            ):
                return cst.SimpleStatementLine(
                    body=[
                        cst.Assign(
                            targets=[
                                cst.AssignTarget(
                                    target=cst.Name(value="detector_pattern")
                                )
                            ],
                            value=value,
                        )
                    ]
                )

        raise ValueError("Could not find detector pattern for codemod")

    def create_change_description(
        self, metadata: dict
    ) -> cst.SimpleStatementLine | None:
        if (
            "description" in metadata
            and "change_description" not in metadata
            and "CHANGE_DESCRIPTION" not in metadata
        ):
            match metadata["description"]:
                case cst.SimpleString() as description:
                    return cst.SimpleStatementLine(
                        body=[
                            cst.Assign(
                                targets=[
                                    cst.AssignTarget(
                                        target=cst.Name(value="change_description")
                                    )
                                ],
                                value=description,
                            )
                        ]
                    )

        return None

    def leave_Assert(self, original: cst.Assert, updated: cst.Assert):
        match original:
            case cst.Assert(
                test=cst.Comparison(
                    left=cst.Call(
                        func=cst.Name(value="len"),
                        args=[
                            cst.Arg(
                                value=cst.Attribute(
                                    value=cst.Attribute(
                                        value=cst.Name(value="self"),
                                        attr=cst.Name(value="file_context"),
                                    ),
                                    attr=cst.Name(value="codemod_changes"),
                                )
                            )
                        ],
                    )
                )
            ):
                return cst.RemoveFromParent()
        return updated

    def leave_Name(self, original: cst.Name, updated: cst.Name) -> cst.Name:
        if original.value == "CHANGE_DESCRIPTION":
            return updated.with_changes(value="change_description")

        return updated

    def leave_ImportFrom(self, original: cst.ImportFrom, updated: cst.ImportFrom):
        match original:
            case cst.ImportFrom(
                module=cst.Attribute(
                    value=cst.Attribute(
                        value=cst.Name(value="codemodder"),
                        attr=cst.Name(value="codemods"),
                    ),
                    attr=cst.Name(value="api"),
                )
            ):
                return cst.RemoveFromParent()

        return updated

    def leave_ClassDef(self, original: cst.ClassDef, new: cst.ClassDef) -> cst.ClassDef:
        new_bases: list[cst.Arg] = [
            (
                base.with_changes(value=cst.Name(self.new_api_class))
                if self.find_base_name(base.value)
                in (
                    "codemodder.codemods.api.BaseCodemod",
                    "codemodder.codemods.api.SemgrepCodemod",
                )
                else base
            )
            for base in original.bases
        ]

        if all(base.value.value != self.new_api_class for base in new_bases):
            return new

        self.add_needed_import(self.new_api_module, obj=self.new_api_class)

        metadata = {}
        new_body = []
        for stmt in new.body.body:
            match stmt:
                case cst.SimpleStatementLine(body=(cst.Assign() as assign,)):
                    if result := self.find_metadata(assign):
                        key, value = result
                        if key == "change_description":
                            new_body.append(stmt)
                            continue

                        metadata[key.lower()] = value
                        continue
                case cst.FunctionDef(
                    name=cst.Name(value="rule"),
                    body=body,
                ):
                    new_body.append(self.create_rule(body))
                    continue

            new_body.append(stmt)

        if not metadata or "name" not in metadata:
            return new

        new_metadata, has_references = self._build_metadata(metadata)
        new_body.insert(0, new_metadata)

        if change_description := self.create_change_description(metadata):
            new_body.insert(1, change_description)

        self.add_needed_import(self.new_api_module, obj="SimpleCodemod")
        self.add_needed_import(self.new_api_module, obj="Metadata")
        if has_references:
            self.add_needed_import(self.new_api_module, obj="Reference")
        self.add_needed_import(self.new_api_module, obj="ReviewGuidance")

        self.remove_unused_import(original)

        new_body = new.body.with_changes(body=new_body)
        return new.with_changes(bases=new_bases, body=new_body)


def make_metadata_arg(
    metadata: dict,
    metadata_key: str,
    value: cst.BaseExpression | None = None,
    last: bool = False,
) -> cst.Arg:
    return cst.Arg(
        value=value or metadata[metadata_key],
        keyword=cst.Name(value=metadata_key),
        equal=RefactorNewApi.no_whitespace_assign,
        whitespace_after_arg=cst.ParenthesizedWhitespace(
            indent=True,
            last_line=cst.SimpleWhitespace("" if last else "    "),
        ),
        comma=cst.Comma(whitespace_after=cst.SimpleWhitespace("")),
    )


def build_references(old_refs: cst.List) -> cst.List:
    new_refs: list[cst.Call] = []
    for ref in old_refs.elements:
        match ref:
            case cst.Element(value=cst.Dict(elements=elements)):
                args = [
                    cst.Arg(
                        keyword=cst.Name(value=elm.key.raw_value),
                        value=elm.value,
                        equal=RefactorNewApi.no_whitespace_assign,
                    )
                    for elm in elements
                    if elm.value.raw_value
                ]
                new_refs.append(
                    cst.Call(
                        func=cst.Name(value="Reference"),
                        args=args,
                    )
                )

    return cst.List(
        elements=[
            cst.Element(
                value=ref,
                comma=cst.Comma(
                    whitespace_after=cst.ParenthesizedWhitespace(
                        indent=True,
                        first_line=cst.TrailingWhitespace(newline=cst.Newline()),
                    )
                ),
            )
            for ref in new_refs
        ],
        lbracket=cst.LeftSquareBracket(
            whitespace_after=cst.ParenthesizedWhitespace(
                indent=True,
                last_line=cst.SimpleWhitespace(" " * 8),
            ),
        ),
        rbracket=cst.RightSquareBracket(
            whitespace_before=cst.ParenthesizedWhitespace(
                indent=True,
                last_line=cst.SimpleWhitespace(" " * 4),
            ),
        ),
    )
