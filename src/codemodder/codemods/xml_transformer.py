import mmap
from tempfile import TemporaryFile
from xml.sax import SAXParseException, handler
from xml.sax.handler import LexicalHandler
from xml.sax.saxutils import XMLGenerator
from xml.sax.xmlreader import Locator

from defusedxml.sax import make_parser

from codemodder.codemods.base_transformer import BaseTransformerPipeline
from codemodder.codetf import Change, ChangeSet
from codemodder.context import CodemodExecutionContext
from codemodder.diff import create_diff
from codemodder.file_context import FileContext
from codemodder.result import Result


class XMLTransformer(XMLGenerator, LexicalHandler):
    """
    Given a XML file, generates the same file but formatted.
    """

    change_description = ""

    def __init__(
        self,
        out,
        encoding: str = "utf-8",
        short_empty_elements: bool = False,
        results: list[Result] | None = None,
    ) -> None:
        self.results = results
        self.changes: list[Change] = []
        self._my_locator = Locator()
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
        self._write("<!CDATA[")  # type: ignore

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
                if location.start.line == line and location.start.column - 1 == column:
                    return True
        return False

    def add_change(self, line):
        self.changes.append(
            Change(lineNumber=line, description=self.change_description)
        )


class ElementAttributeXMLTransformer(XMLTransformer):
    """
    Changes the element and its attributes to the values provided in a given dict. For any attribute missing in the dict will stay the same as the original.
    """

    def __init__(
        self,
        out,
        name_attributes_map: dict[str, dict[str, str]],
        encoding: str = "iso-8859-1",
        short_empty_elements: bool = False,
        results: list[Result] | None = None,
    ) -> None:
        self.name_attributes_map = name_attributes_map
        super().__init__(out, encoding, short_empty_elements, results)

    def startElement(self, name, attrs):
        new_attrs = attrs
        if self.event_match_result():
            if name in self.name_attributes_map:
                new_attrs = self.name_attributes_map[name]
                self.add_change(self._my_locator.getLineNumber())
        super().startElement(name, new_attrs)


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
        if file_context.file_path.suffix.lower() not in (".config", ".xml"):
            return None

        changes = []
        with TemporaryFile("w+") as output_file:

            # this will fail fast for files that are not XML
            try:
                transformer_instance = self.xml_transformer(
                    out=output_file, results=results
                )
                parser = make_parser()
                parser.setContentHandler(transformer_instance)
                parser.setProperty(
                    handler.property_lexical_handler, transformer_instance
                )
                parser.parse(file_context.file_path)
                changes = transformer_instance.changes
                output_file.seek(0)

            except SAXParseException:
                return None

            diff = ""
            with open(file_context.file_path, "r") as original:
                # don't calculate diff if no changes were reported
                # TODO there's a failure potential here for very large files
                diff = (
                    create_diff(
                        original.readlines(),
                        output_file.readlines(),
                    )
                    if changes
                    else ""
                )

            if not context.dry_run:
                with open(file_context.file_path, "w+b") as original:
                    # mmap can't map empty files, write something first
                    original.write(b"a")
                    # copy contents of result into original file
                    # the snippet below preserves the original file metadata and accounts for large files.
                    output_file.seek(0)
                    output_mmap = mmap.mmap(output_file.fileno(), 0)

                    original.truncate()
                    original_mmap = mmap.mmap(original.fileno(), 0)
                    original_mmap.resize(len(output_mmap))
                    original_mmap[:] = output_mmap
                    original_mmap.flush()

            return ChangeSet(
                path=str(file_context.file_path.relative_to(context.directory)),
                diff=diff,
                changes=changes,
            )
