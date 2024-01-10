# -*- coding: utf-8 -*-
"""Better HTML formatter for Pygments.

Copyright © 2020-2024, Chris Warrick.
License: 3-clause BSD.
Portions copyright © 2006-2019, the Pygments authors. (2-clause BSD).
"""

__all__ = ["BetterHtmlFormatter"]
__version__ = "0.1.4"

import enum
import re
import warnings

from pygments.formatters.html import HtmlFormatter

MANY_SPACES = re.compile("(  +)")


def _sp_to_nbsp(m):
    return "&nbsp;" * (m.end() - m.start())


class BetterLinenos(enum.Enum):
    TABLE = "table"
    OL = "ol"


class BetterHtmlFormatter(HtmlFormatter):
    r"""
    Format tokens as HTML 4 ``<span>`` tags, with alternate formatting styles.

    * ``linenos = 'table'`` renders each line of code in a separate table row
    * ``linenos = 'ol'`` renders each line in a <li> element (inside <ol>)

    Both options allow word wrap and don't include line numbers when copying.
    """

    name = "HTML"
    aliases = ["html"]
    filenames = ["*.html", "*.htm"]

    def __init__(self, **options):
        """Initialize the formatter."""
        super().__init__(**options)
        self.linenos_name = self.options.get("linenos", "table")
        if self.linenos_name is False:
            self.linenos_val = False
            self.linenos = 0
        elif self.linenos_name is True:
            self.linenos_name = "table"
        if self.linenos_name is not False:
            self.linenos_val = BetterLinenos(self.linenos_name)
            self.linenos = 2 if self.linenos_val == BetterLinenos.OL else 1

    def get_style_defs(self, arg=None, wrapper_classes=None):
        """Generate CSS style definitions.

        Return CSS style definitions for the classes produced by the current
        highlighting style. ``arg`` can be a string or list of selectors to
        insert before the token type classes. ``wrapper_classes`` are a list of
        classes for the wrappers, defaults to the ``cssclass`` option.
        """
        base = super().get_style_defs(arg)
        new_styles = (
            ("{0} table, {0} tr, {0} td", "border-spacing: 0; border-collapse: separate; padding: 0"),
            ("{0} pre", "white-space: pre-wrap; line-height: normal"),
            (
                "{0}table td.linenos",
                "vertical-align: top; padding-left: 10px; padding-right: 10px; user-select: none; -webkit-user-select: none",
            ),
            # Hack for Safari (user-select does not affect copy-paste)
            ("{0}table td.linenos code:before", "content: attr(data-line-number)"),
            ("{0}table td.code", "overflow-wrap: normal; border-collapse: collapse"),
            (
                "{0}table td.code code",
                "overflow: unset; border: none; padding: 0; margin: 0; white-space: pre-wrap; line-height: unset; background: none",
            ),
            ("{0} .lineno.nonumber", "list-style: none"),
        )
        new_styles_code = []
        if wrapper_classes is None:
            wrapper_classes = ["." + self.cssclass]
        for cls, rule in new_styles:
            new_styles_code.append(", ".join(cls.format(c) for c in wrapper_classes) + " { " + rule + " }")
        return base + "\n" + "\n".join(new_styles_code)

    def _wrap_tablelinenos(self, inner):
        lncount = 0
        codelines = []
        for t, line in inner:
            if t:
                lncount += 1
            codelines.append(line)

        fl = self.linenostart
        mw = len(str(lncount + fl - 1))
        sp = self.linenospecial
        st = self.linenostep
        la = self.lineanchors
        aln = self.anchorlinenos
        nocls = self.noclasses
        if sp:
            lines = []

            for i in range(fl, fl + lncount):
                line_before = ""
                line_after = ""
                if i % st == 0:
                    if i % sp == 0:
                        if aln:
                            line_before = '<a href="#%s-%d" class="special">' % (la, i)
                            line_after = "</a>"
                        else:
                            line_before = '<span class="special">'
                            line_after = "</span>"
                    elif aln:
                        line_before = '<a href="#%s-%d">' % (la, i)
                        line_after = "</a>"
                    lines.append((line_before, "%*d" % (mw, i), line_after))
                else:
                    lines.append(("", "", ""))
        else:
            lines = []
            for i in range(fl, fl + lncount):
                line_before = ""
                line_after = ""
                if i % st == 0:
                    if aln:
                        line_before = '<a href="#%s-%d">' % (la, i)
                        line_after = "</a>"
                    lines.append((line_before, "%*d" % (mw, i), line_after))
                else:
                    lines.append(("", "", ""))

        yield 0, '<div class="%s"><table class="%stable">' % (
            self.cssclass,
            self.cssclass,
        )
        for lndata, cl in zip(lines, codelines):
            ln_b, ln, ln_a = lndata
            cl = MANY_SPACES.sub(_sp_to_nbsp, cl)
            if nocls:
                yield 0, (
                    '<tr><td class="linenos linenodiv" style="background-color: #f0f0f0; padding-right: 10px">' + ln_b +
                    '<code data-line-number="' + ln + '"></code>' + ln_a + '</td><td class="code"><code>' + cl + "</code></td></tr>"
                )
            else:
                yield 0, (
                    '<tr><td class="linenos linenodiv">' + ln_b + '<code data-line-number="' + ln +
                    '"></code>' + ln_a + '</td><td class="code"><code>' + cl + "</code></td></tr>"
                )
        yield 0, "</table></div>"

    def _wrap_inlinelinenos(self, inner):
        # Override with new method
        return self._wrap_ollineos(self, inner)

    def _wrap_ollinenos(self, inner):
        lines = inner
        sp = self.linenospecial
        st = self.linenostep or 1
        num = self.linenostart

        if self.anchorlinenos:
            warnings.warn("anchorlinenos is not supported for linenos='ol'.")

        yield 0, "<ol>"
        if self.noclasses:
            if sp:
                for t, line in lines:
                    if num % sp == 0:
                        style = "background-color: #ffffc0; padding: 0 5px 0 5px"
                    else:
                        style = "background-color: #f0f0f0; padding: 0 5px 0 5px"
                    if num % st != 0:
                        style += "; list-style: none"
                    yield 1, '<li style="%s" value="%s">' % (style, num,) + line + "</li>"
                    num += 1
            else:
                for t, line in lines:
                    yield 1, (
                        '<li style="background-color: #f0f0f0; padding: 0 5px 0 5px%s" value="%s">'
                        % (("; list-style: none" if num % st != 0 else ""), num) + line + "</li>"
                    )
                    num += 1
        elif sp:
            for t, line in lines:
                yield 1, '<li class="lineno%s%s" value="%s">' % (
                    " special" if num % sp == 0 else "",
                    " nonumber" if num % st != 0 else "",
                    num,
                ) + line + "</li>"
                num += 1
        else:
            for t, line in lines:
                yield 1, '<li class="lineno%s" value="%s">' % (
                    "" if num % st != 0 else " nonumber",
                    num,
                ) + line + "</li>"
                num += 1

        yield 0, "</ol>"

    def format_unencoded(self, tokensource, outfile):
        """Format code and write to outfile.

        The formatting process uses several nested generators; which of
        them are used is determined by the user's options.

        Each generator should take at least one argument, ``inner``,
        and wrap the pieces of text generated by this.

        Always yield 2-tuples: (code, text). If "code" is 1, the text
        is part of the original tokensource being highlighted, if it's
        0, the text is some piece of wrapping. This makes it possible to
        use several different wrappers that process the original source
        linewise, e.g. line number generators.
        """
        if self.linenos_val is False:
            return super().format_unencoded(tokensource, outfile)
        source = self._format_lines(tokensource)
        if self.hl_lines:
            source = self._highlight_lines(source)
        if not self.nowrap:
            if self.linenos_val == BetterLinenos.OL:
                source = self._wrap_ollinenos(source)
            if self.lineanchors:
                source = self._wrap_lineanchors(source)
            if self.linespans:
                source = self._wrap_linespans(source)
            if self.linenos_val == BetterLinenos.TABLE:
                source = self._wrap_tablelinenos(source)
            if self.linenos_val == BetterLinenos.OL:
                source = self.wrap(source, outfile)
            if self.full:
                source = self._wrap_full(source, outfile)

        for t, piece in source:
            outfile.write(piece)
