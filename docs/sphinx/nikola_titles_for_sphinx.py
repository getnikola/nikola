import sphinx.parsers
from docutils.statemachine import StringList
from typing import TYPE_CHECKING, Any, Dict, List, Type, Union

if TYPE_CHECKING:
    from sphinx.application import Sphinx

TITLE_MARKER = ".. title:"


class NikolaTitlesRSTParser(sphinx.parsers.RSTParser):
    def decorate(self, content: StringList) -> None:
        """Preprocess reST content before parsing."""
        super().decorate(content)
        for line in content[:20]:
            if line.startswith(TITLE_MARKER):
                title = line[len(TITLE_MARKER) :].strip()
                fence = "=" * len(title)
                content.insert(0, "", "<generated>", 0)
                content.insert(0, fence, "<generated>", 0)
                content.insert(0, title, "<generated>", 0)
                content.insert(0, fence, "<generated>", 0)


def setup(app: "Sphinx") -> Dict[str, Any]:
    app.add_source_parser(NikolaTitlesRSTParser, override=True)

    return {
        "version": "0.1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
