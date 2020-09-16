#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
# Quotebacks extension for Python-Markdown

Use by including `QuotebacksExtension()` in the extensions list.

Converts Markdown of the form:

```markdown
> QUOTED-CONTENT
>
> -- AUTHOR, [LINKTEXT](URL)
```

to the quotebacks format.
"""


import logging
import markdown
import re
import sys
import xml.etree.ElementTree as ET

from markdown import Extension

from nikola.plugin_categories import MarkdownExtension

LOGGER = logging.getLogger("quotebacks-mdx")

# If required, add this at the bottom of the page
QUOTEBACKS_SCRIPT_TAG = """<script note="" src="https://cdn.jsdelivr.net/gh/Blogger-Peer-Review/quotebacks@1/quoteback.js"></script>"""


class QuotebacksExtension(MarkdownExtension, Extension):
    """Python-Markdown extension that wraps QuotebacksProcessor and
    makes it available to transform HTML docs.
    """

    def __init__(self, **kwargs):
        """ Override the init and set self.config according to:

           https://python-markdown.github.io/extensions/api/

        Keys set in self.config can be passed in as kwargs to this
        extension to override the default values. These are available
        from self.getConfigs() (as a dict) later.
        """
        # self.config["key"] = [
        #    [],  # default value
        #    "Sets ...",   # description of parameter
        # ]
        self.config = {}

        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        # Run with a priority of 19.
        # Needs to run:
        # - AFTER a tags have been created
        # - BEFORE smartypants
        # Pass in the dictionary of config variables: this tree processor has overridden
        # its init to accept these.
        md.treeprocessors.register(
            QuotebacksProcessor(md, self.getConfigs()), "quotebacks", 19
        )


class QuotebacksProcessor(markdown.treeprocessors.Treeprocessor):
    """Python-Markdown processor that changes the blockquotes in the output document to
    match the Quotebacks format.

    Rules:

    - there must be more than one child of the blockquote
    - the final child must be a p element
    - the p element must have the pattern:

       <p>-- AUTHOR, <a href="CITE_URL">TITLE</a></p>

    The source Markdown format for this is:

       > ...
       >
       > -- AUTHOR, [TITLE](CITE_URL)
    """

    def __init__(self, md, config):
        """ Usually a tree processor won't take a config dict, but here
        we're overriding init to accept one. This is for future options.

        Stash the markdown instance for later.
        """
        self.config = config
        self.md = md

        # We record whether there were quotebacks found
        self.md.quotebacks_found = False

        super().__init__(md)

    def run(self, root):
        # Iterate over all blockquote elements
        for bq in root.iter("blockquote"):
            # blockquote must have >1 children
            if len(bq) <= 1:
                LOGGER.info("blockquote must have >1 children")
                continue

            # blockquote's final child must be a paragraph
            if bq[-1].tag != "p":
                LOGGER.info("blockquote's final child must be a p tag")
                continue

            # Keep the paragraph element handy. It must look like
            # '-- AUTHOR <a href="CITE_URL">TITLE</a>'
            p_elem = bq[-1]

            if not (len(p_elem) == 1 and p_elem[0].tag == "a"):
                LOGGER.info("Final p must have one child and it must be an a tag")
                continue

            a_elem = p_elem[0]
            title = a_elem.text
            cite_url = a_elem.get("href", None)

            if not title:
                LOGGER.info("Final a tag must have text for the title")
                continue

            if not cite_url:
                LOGGER.info("Final a tag must have an href for the cite URL")
                continue

            # There must be no tail text
            if p_elem.tail is not None:
                LOGGER.info("p must have no tail text")
                continue

            # The start text must follow a strict pattern
            if not p_elem.text:
                LOGGER.info("p must have start text")

            m = re.match(r"^-- (?P<author>.+),\s+$", p_elem.text)
            if not m:
                LOGGER.info("p must match the pattern '-- AUTHOR, '")
                continue

            author = m.groupdict()["author"]

            # Time to change the document!
            # First, remove the original element
            bq.remove(p_elem)

            # Build the replacement tag, using the original elements where possible
            footer = ET.SubElement(bq, "footer",)
            footer.text = p_elem.text
            cite = ET.SubElement(footer, "cite")
            cite.append(a_elem)

            # Set bq Attributes
            attrib = {
                "class": "quoteback",
                "data-title": title,
                "data-author": author,
                "cite": cite_url,
            }

            [bq.set(k, v) for k, v in attrib.items()]

            LOGGER.info("Successful: blockquote -> quoteback")
            self.md.quotebacks_found = True


def test():
    # Log everything
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    # Use UTF-8 instead of the defaut HTML entities
    # https://python-markdown.github.io/extensions/smarty/
    smarty_substitutions = {
        "left-single-quote": "‘",
        "right-single-quote": "’",
        "left-double-quote": "“",
        "right-double-quote": "”",
        "left-angle-quote": "«",
        "right-angle-quote": "»",
        "ellipsis": "…",
        "ndash": "–",
        "mdash": "—",
    }

    renderer = markdown.Markdown(
        output_format="html5",
        tab_length=2,
        extensions=["smarty", "attr_list", QuotebacksExtension()],
        extension_configs={"smarty": {"substitutions": smarty_substitutions}},
    )

    source_md = """# Test Document

Hello, World!

> The text renaissance is an actual _renaissance._ It's a story of history-inspired
> renewal in a very fundamental way: exciting recent developments are due in part to a new
> generation of young product visionaries circling back to the early history of digital
> text, rediscovering old, abandoned ideas, and reimagining the bleeding edge in terms of
> the unexplored adjacent possible of the 80s and 90s.
>
> -- @ribbonfarm, [A Text Renaissance](https://www.ribbonfarm.com/2020/02/24/a-text-renaissance/)
"""

    expected_html = """<h1>Test Document</h1>
<p>Hello, World!</p>
<blockquote cite="https://www.ribbonfarm.com/2020/02/24/a-text-renaissance/" class="quoteback" data-author="@ribbonfarm" data-title="A Text Renaissance">
<p>The text renaissance is an actual <em>renaissance.</em> It’s a story of history-inspired
renewal in a very fundamental way: exciting recent developments are due in part to a new
generation of young product visionaries circling back to the early history of digital
text, rediscovering old, abandoned ideas, and reimagining the bleeding edge in terms of
the unexplored adjacent possible of the 80s and 90s.</p>
<footer>– @ribbonfarm, <cite><a href="https://www.ribbonfarm.com/2020/02/24/a-text-renaissance/">A Text Renaissance</a></cite></footer>
</blockquote>"""

    html = renderer.convert(source_md)

    assert renderer.quotebacks_found is True

    print(html)

    if html != expected_html:
        LOGGER.error("Generated HTML does not match expected HTML")
    else:
        LOGGER.info("-- SUCCESS --")


if __name__ == "__main__":
    # Runs tests only if run as a script
    test()
