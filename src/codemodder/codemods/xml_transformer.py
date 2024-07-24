from dataclasses import dataclass, field
from tempfile import TemporaryFile
from xml.sax import handler
from xml.sax.handler import LexicalHandler
from xml.sax.saxutils import XMLGenerator
from xml.sax.xmlreader import AttributesImpl, Locator

from defusedxml.sax import make_parser

from codemodder.codemods.base_transformer import BaseTransformerPipeline
from codemodder.codetf import Change, ChangeSet
from codemodder.context import CodemodExecutionContext
from codemodder.diff import create_diff
from codemodder.file_context import FileContext
from codemodder.logging import logger
from codemodder.result import Result


class XMLTransformer(XMLGenerator, LexicalHandler):
    """
    Given a XML file, generates the same file but formatted.
    """

    change_description = ""

    def __init__(
        self,
        out,
        file_context: FileContext,
        encoding: str = "utf-8",
        short_empty_elements: bool = False,
        results: list[Result] | None = None,
        line_only_matching=False,
    ) -> None:
        self.file_context = file_context
        self.results = results
        self.changes: list[Change] = []
        self._my_locator = Locator()
        self.line_only_matching = line_only_matching
        super().__init__(out, encoding, short_empty_elements)

    def startElement(self, name, attrs):
        super().startElement(name, attrs)

    def endElement(self, name):
        super().endElement(name)

    def characters(self, content):
        super().characters(content)

    def skippedEntity(self, name: str) -> None:
        super().skippedEntity(name)

    def comment(self, content: str):
        self._write(f"<!--{content}-->\n")  # type: ignore

    def startCDATA(self):
        self._write("<![CDATA[")  # type: ignore

    def endCDATA(self):
        self._write("]]>")  # type: ignore

    def startDTD(self, name: str, public_id: str | None, system_id: str | None):
        self._write(f'<!DOCTYPE {name} PUBLIC "{public_id}" "{system_id}">\n')  # type: ignore
        return super().startDTD(name, public_id, system_id)

    def endDTD(self) -> object:
        return super().endDTD()

    def setDocumentLocator(self, locator: Locator) -> None:
        self._my_locator = locator

    def event_match_result(self) -> bool:
        """
        Returns True if the current event matches any result.
        """
        line = self._my_locator.getLineNumber()
        column = self._my_locator.getColumnNumber()
        return self.match_result(line, column)

    def match_result(self, line, column) -> bool:
        if self.results is None:
            return True
        for result in self.results or []:
            for location in result.locations:
                # No two elements can have the same start but different ends.
                # It suffices to only match the start.
                if (self.line_only_matching and location.start.line == line) or (
                    location.start.line == line and location.start.column - 1 == column
                ):
                    return True
        return False

    def add_change(self, line):
        self.changes.append(
            Change(
                lineNumber=line,
                description=self.change_description,
                findings=self.file_context.get_findings_for_location(line),
            )
        )


class ElementAttributeXMLTransformer(XMLTransformer):
    """
    Changes the element and its attributes to the values provided in a given dict. For any attribute missing in the dict will stay the same as the original.
    """

    def __init__(
        self,
        out,
        file_context: FileContext,
        name_attributes_map: dict[str, dict[str, str]],
        encoding: str = "utf-8",
        short_empty_elements: bool = False,
        results: list[Result] | None = None,
        line_only_matching=False,
    ) -> None:
        self.name_attributes_map = name_attributes_map
        super().__init__(
            out,
            file_context,
            encoding,
            short_empty_elements,
            results,
            line_only_matching,
        )

    def startElement(self, name, attrs):
        new_attrs: AttributesImpl = attrs
        if self.event_match_result() and name in self.name_attributes_map:
            new_attrs = AttributesImpl(attrs._attrs | self.name_attributes_map[name])
            self.add_change(self._my_locator.getLineNumber())
        super().startElement(name, new_attrs)


@dataclass
class NewElement:
    name: str
    parent_name: str
    content: str = ""
    attributes: dict[str, str] = field(default_factory=dict)


class NewElementXMLTransformer(XMLTransformer):
    """
    Adds new elements to the XML file at specified locations.
    """

    def __init__(
        self,
        out,
        file_context: FileContext,
        encoding: str = "utf-8",
        short_empty_elements: bool = False,
        results: list[Result] | None = None,
        new_elements: list[NewElement] | None = None,
    ) -> None:
        super().__init__(out, file_context, encoding, short_empty_elements, results)
        self.new_elements = new_elements or []

    def startElement(self, name, attrs):
        super().startElement(name, attrs)

    def endElement(self, name):
        for new_element in self.new_elements:
            if new_element.parent_name == name:
                self.add_new_element(new_element)
                self.add_change(self._my_locator.getLineNumber())
        super().endElement(name)

    def add_new_element(self, new_element: NewElement):
        attrs = AttributesImpl(new_element.attributes or {})
        super().startElement(new_element.name, attrs)
        if isinstance(new_element.content, NewElement):
            self.add_new_element(new_element.content)
        else:
            super().characters(new_element.content)
        super().endElement(new_element.name)


class XMLTransformerPipeline(BaseTransformerPipeline):

    def __init__(self, xml_transformer: type[XMLTransformer]):
        super().__init__()
        self.xml_transformer = xml_transformer

    def apply(
        self,
        context: CodemodExecutionContext,
        file_context: FileContext,
        results: list[Result] | None,
    ) -> ChangeSet | None:
        with TemporaryFile("w+") as output_file:
            # this will fail fast for files that are not XML
            try:
                transformer_instance = self.xml_transformer(
                    out=output_file,
                    file_context=file_context,
                    results=results,
                )
                parser = make_parser()
                parser.setContentHandler(transformer_instance)
                parser.setProperty(
                    handler.property_lexical_handler, transformer_instance
                )
                parser.parse(file_path := file_context.file_path)
                changes = transformer_instance.changes
                output_file.seek(0)
            except Exception:
                file_context.add_failure(
                    file_path, reason := "Failed to parse XML file"
                )
                logger.exception("%s %s", reason, file_path)
                return None

            if not changes:
                return None

            new_lines = output_file.readlines()
            with open(file_path, "r") as original:
                # TODO there's a failure potential here for very large files
                diff = create_diff(
                    original.readlines(),
                    new_lines,
                )

            if not context.dry_run:
                with open(file_path, "w+") as original:
                    original.writelines(new_lines)

            return ChangeSet(
                path=str(file_path.relative_to(context.directory)),
                diff=diff,
                changes=changes,
            )
