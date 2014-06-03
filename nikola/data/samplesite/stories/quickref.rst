.. title: A reStructuredText Reference
.. slug: quickref
.. date: 2012-03-30 23:00:00 UTC-03:00
.. tags: 
.. link: 
.. description: 

.. raw:: html

        <div class="alert alert-info pull-right" style="margin-left: 2em;">
        <h2><a name="contents">Contents</a></h2>

        <ul>
        <li><a href="#inline-markup">Inline Markup</a></li>
        <li><a href="#escaping">Escaping with Backslashes</a></li>
        <li><a href="#section-structure">Section Structure</a></li>
        <li><a href="#paragraphs">Paragraphs</a></li>
        <li><a href="#bullet-lists">Bullet Lists</a></li>
        <li><a href="#enumerated-lists">Enumerated Lists</a></li>
        <li><a href="#definition-lists">Definition Lists</a></li>
        <li><a href="#field-lists">Field Lists</a></li>
        <li><a href="#option-lists">Option Lists</a></li>
        <li><a href="#literal-blocks">Literal Blocks</a></li>
        <li><a href="#line-blocks">Line Blocks</a></li>
        <li><a href="#block-quotes">Block Quotes</a></li>
        <li><a href="#doctest-blocks">Doctest Blocks</a></li>
        <li><a href="#tables">Tables</a></li>
        <li><a href="#transitions">Transitions</a></li>
        <li><a href="#explicit-markup">Explicit Markup</a>
        <ul>
        <li><a href="#footnotes">Footnotes</a></li>
        <li><a href="#citations">Citations</a></li>
        <li><a href="#hyperlink-targets">Hyperlink Targets</a>
        <ul>
        <li><a href="#external-hyperlink-targets">External Hyperlink Targets</a></li>
        <li><a href="#internal-hyperlink-targets">Internal Hyperlink Targets</a></li>
        <li><a href="#indirect-hyperlink-targets">Indirect Hyperlink Targets</a></li>
        <li><a href="#implicit-hyperlink-targets">Implicit Hyperlink Targets</a></li>
        </ul></li>
        <li><a href="#directives">Directives</a></li>
        <li><a href="#substitution-references-and-definitions">Substitution References and Definitions</a></li>
        <li><a href="#comments">Comments</a></li>
        </ul></li>
        <li><a href="#getting-help">Getting Help</a></li>
        </ul>
        </div>


        <h1>Quick <i>re</i><font size="+4"><tt>Structured</tt></font><i>Text</i></h1>

        <!-- Caveat: if you're reading the HTML for the examples, -->
        <!-- beware that it was hand-generated, not by Docutils/ReST.  -->

        <blockquote>
        <p>Copyright: This document has been placed in the public domain.
        </blockquote>


        <p>The full details of the markup may be found on the
        <a href="http://docutils.sourceforge.net/rst.html">reStructuredText</a>
        page. This document is just intended as a reminder.

        <p>Links that look like "(<a href="#details">details</a>)" point
        into the HTML version of the full <a
        href="http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html">reStructuredText
        specification</a> document.  These are relative links; if they
        don't work, please use the <a
        href="http://docutils.sourceforge.net/docs/user/rst/quickref.html"
        >master "Quick reStructuredText"</a> document.


        <h2><a href="#contents" name="inline-markup" class="backref"
            >Inline Markup</a></h2>

        <p>(<a href="http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#inline-markup">details</a>)

        <p>Inline markup allows words and phrases within text to have
        character styles (like italics and boldface) and functionality
        (like hyperlinks).

        <p><table border="1" bgcolor="#ffffcc" cellpadding="3">
        <thead>
        <tr align="left" bgcolor="#99CCFF">
        <th>Plain text
        <th>Typical result
        <th>Notes
        </thead>
        <tbody>
        <tr valign="top">
        <td nowrap><samp>*emphasis*</samp>
        <td><em>emphasis</em>
        <td>Normally rendered as italics.

        <tr valign="top">
        <td nowrap><samp>**strong&nbsp;emphasis**</samp>
        <td><strong>strong emphasis</strong>
        <td>Normally rendered as boldface.

        <tr valign="top">
        <td nowrap><samp>`interpreted&nbsp;text`</samp>
        <td>(see note at right)
        <td>The rendering and <em>meaning</em> of interpreted text is
        domain- or application-dependent.  It can be used for things
        like index entries or explicit descriptive markup (like program
        identifiers).

        <tr valign="top">
        <td nowrap><samp>``inline&nbsp;literal``</samp>
        <td><code>inline&nbsp;literal</code>
        <td>Normally rendered as monospaced text. Spaces should be
        preserved, but line breaks will not be.

        <tr valign="top">
        <td nowrap><samp>reference_</samp>
        <td><a href="#hyperlink-targets">reference</a>
        <td>A simple, one-word hyperlink reference.  See <a
        href="#hyperlink-targets">Hyperlink Targets</a>.

        <tr valign="top">
        <td nowrap><samp>`phrase reference`_</samp>
        <td><a href="#hyperlink-targets">phrase reference</a>
        <td>A hyperlink reference with spaces or punctuation needs to be
        quoted with backquotes.  See <a
        href="#hyperlink-targets">Hyperlink Targets</a>.

        <tr valign="top">
        <td nowrap><samp>anonymous__</samp>
        <td><a href="#hyperlink-targets">anonymous</a>
        <td>With two underscores instead of one, both simple and phrase
        references may be anonymous (the reference text is not repeated
        at the target).  See <a
        href="#hyperlink-targets">Hyperlink Targets</a>.

        <tr valign="top">
        <td nowrap><samp>_`inline internal target`</samp>
        <td><a name="inline-internal-target">inline internal target</a>
        <td>A crossreference target within text.
        See <a href="#hyperlink-targets">Hyperlink Targets</a>.

        <tr valign="top">
        <td nowrap><samp>|substitution reference|</samp>
        <td>(see note at right)
        <td>The result is substituted in from the <a
        href="#substitution-references-and-definitions">substitution
        definition</a>.  It could be text, an image, a hyperlink, or a
        combination of these and others.

        <tr valign="top">
        <td nowrap><samp>footnote reference [1]_</samp>
        <td>footnote reference <sup><a href="#footnotes">1</a></sup>
        <td>See <a href="#footnotes">Footnotes</a>.

        <tr valign="top">
        <td nowrap><samp>citation reference [CIT2002]_</samp>
        <td>citation reference <a href="#citations">[CIT2002]</a>
        <td>See <a href="#citations">Citations</a>.

        <tr valign="top">
        <td nowrap><samp>http://docutils.sf.net/</samp>
        <td><a href="http://docutils.sf.net/">http://docutils.sf.net/</a>
        <td>A standalone hyperlink.

        </table>

        <p>Asterisk, backquote, vertical bar, and underscore are inline
        delimiter characters. Asterisk, backquote, and vertical bar act
        like quote marks; matching characters surround the marked-up word
        or phrase, whitespace or other quoting is required outside them,
        and there can't be whitespace just inside them. If you want to use
        inline delimiter characters literally, <a href="#escaping">escape
        (with backslash)</a> or quote them (with double backquotes; i.e.
        use inline literals).

        <p>In detail, the reStructuredText specification says that in
        inline markup, the following rules apply to start-strings and
        end-strings (inline markup delimiters):

        <ol>
        <li>The start-string must start a text block or be
        immediately preceded by whitespace or any of&nbsp;
        <samp>' " ( [ {</samp> or&nbsp;<samp>&lt;</samp>.
        <li>The start-string must be immediately followed by non-whitespace.
        <li>The end-string must be immediately preceded by non-whitespace.
        <li>The end-string must end a text block (end of document or
        followed by a blank line) or be immediately followed by whitespace
        or any of&nbsp;<samp>' " . , : ; ! ? - ) ] } / \</samp>
        or&nbsp;<samp>&gt;</samp>.
        <li>If a start-string is immediately preceded by one of&nbsp;
        <samp>' " ( [ {</samp> or&nbsp;<samp>&lt;</samp>, it must not be
        immediately followed by the corresponding character from&nbsp;
        <samp>' " ) ] }</samp> or&nbsp;<samp>&gt;</samp>.
        <li>An end-string must be separated by at least one
        character from the start-string.
        <li>An <a href="#escaping">unescaped</a> backslash preceding a
        start-string or end-string will disable markup recognition, except
        for the end-string of inline literals.
        </ol>

        <p>Also remember that inline markup may not be nested (well,
        except that inline literals can contain any of the other inline
        markup delimiter characters, but that doesn't count because
        nothing is processed).

        <h2><a href="#contents" name="escaping" class="backref"
            >Escaping with Backslashes</a></h2>

        <p>(<a
        href="http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#escaping-mechanism">details</a>)

        <p>reStructuredText uses backslashes ("\") to override the special
        meaning given to markup characters and get the literal characters
        themselves. To get a literal backslash, use an escaped backslash
        ("\\"). For example:

        <p><table border="1" width="100%" bgcolor="#ffffcc" cellpadding="3">
        <thead>
        <tr align="left" bgcolor="#99CCFF">
        <th width="50%">Raw reStructuredText
        <th width="50%">Typical result
        </thead>
        <tbody>
        <tr valign="top"><td>
            <samp>*escape*&nbsp;``with``&nbsp;"\"</samp>
        <td><em>escape</em> <samp>with</samp> ""
        <tr valign="top"><td>
            <samp>\*escape*&nbsp;\``with``&nbsp;"\\"</samp>
        <td>*escape* ``with`` "\"
        </table>

        <p>In Python strings it will, of course, be necessary
        to escape any backslash characters so that they actually
        <em>reach</em> reStructuredText.
        The simplest way to do this is to use raw strings:

        <p><table border="1" width="100%" bgcolor="#ffffcc" cellpadding="3">
        <thead>
        <tr align="left" bgcolor="#99CCFF">
        <th width="50%">Python string
        <th width="50%">Typical result
        </thead>
        <tbody>
        <tr valign="top"><td>
            <samp>r"""\*escape*&nbsp;\`with`&nbsp;"\\""""</samp>
        <td>*escape* `with` "\"
        <tr valign="top"><td>
            <samp>&nbsp;"""\\*escape*&nbsp;\\`with`&nbsp;"\\\\""""</samp>
        <td>*escape* `with` "\"
        <tr valign="top"><td>
            <samp>&nbsp;"""\*escape*&nbsp;\`with`&nbsp;"\\""""</samp>
        <td><em>escape</em> with ""
        </table>

        <h2><a href="#contents" name="section-structure" class="backref"
            >Section Structure</a></h2>

        <p>(<a href="http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#sections">details</a>)

        <p><table border="1" width="100%" bgcolor="#ffffcc" cellpadding="3">
        <thead>
        <tr align="left" bgcolor="#99CCFF">
        <th width="50%">Plain text
        <th width="50%">Typical result
        </thead>
        <tbody>
        <tr valign="top">
        <td>
    <samp>=====</samp>
    <br><samp>Title</samp>
    <br><samp>=====</samp>
    <br><samp>Subtitle</samp>
    <br><samp>--------</samp>
    <br><samp>Titles&nbsp;are&nbsp;underlined&nbsp;(or&nbsp;over-</samp>
    <br><samp>and&nbsp;underlined)&nbsp;with&nbsp;a&nbsp;printing</samp>
    <br><samp>nonalphanumeric&nbsp;7-bit&nbsp;ASCII</samp>
    <br><samp>character.&nbsp;Recommended&nbsp;choices</samp>
    <br><samp>are&nbsp;"``=&nbsp;-&nbsp;`&nbsp;:&nbsp;'&nbsp;"&nbsp;~&nbsp;^&nbsp;_&nbsp;*&nbsp;+&nbsp;#&nbsp;&lt;&nbsp;&gt;``".</samp>
    <br><samp>The&nbsp;underline/overline&nbsp;must&nbsp;be&nbsp;at</samp>
    <br><samp>least&nbsp;as&nbsp;long&nbsp;as&nbsp;the&nbsp;title&nbsp;text.</samp>
    <br><samp></samp>
    <br><samp>A&nbsp;lone&nbsp;top-level&nbsp;(sub)section</samp>
    <br><samp>is&nbsp;lifted&nbsp;up&nbsp;to&nbsp;be&nbsp;the&nbsp;document's</samp>
    <br><samp>(sub)title.</samp>

        <td>
            <font size="+2"><strong>Title</strong></font>
            <p><font size="+1"><strong>Subtitle</strong></font>
            <p>Titles are underlined (or over-
            and underlined) with a printing
            nonalphanumeric 7-bit ASCII
            character. Recommended choices
            are "<samp>= - ` : ' " ~ ^ _ * + # &lt; &gt;</samp>".
            The underline/overline must be at
            least as long as the title text.
            <p>A lone top-level (sub)section is
            lifted up to be the document's
            (sub)title.
        </table>

        <h2><a href="#contents" name="paragraphs" class="backref"
            >Paragraphs</a></h2>

        <p>(<a href="http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#paragraphs">details</a>)

        <p><table border="1" width="100%" bgcolor="#ffffcc" cellpadding="3">
        <thead>
        <tr align="left" bgcolor="#99CCFF">
        <th width="50%">Plain text
        <th width="50%">Typical result
        </thead>
        <tbody>
        <tr valign="top">
        <td>
    <p><samp>This&nbsp;is&nbsp;a&nbsp;paragraph.</samp>

    <p><samp>Paragraphs&nbsp;line&nbsp;up&nbsp;at&nbsp;their&nbsp;left</samp>
    <br><samp>edges,&nbsp;and&nbsp;are&nbsp;normally&nbsp;separated</samp>
    <br><samp>by&nbsp;blank&nbsp;lines.</samp>

        <td>
            <p>This is a paragraph.

            <p>Paragraphs line up at their left edges, and are normally
            separated by blank lines.

        </table>

        <h2><a href="#contents" name="bullet-lists" class="backref"
            >Bullet Lists</a></h2>

        <p>(<a href="http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#bullet-lists">details</a>)

        <p><table border="1" width="100%" bgcolor="#ffffcc" cellpadding="3">
        <thead>
        <tr align="left" bgcolor="#99CCFF">
        <th width="50%">Plain text
        <th width="50%">Typical result
        </thead>
        <tbody>
        <tr valign="top">
        <td>
    <samp>Bullet&nbsp;lists:</samp>

    <p><samp>-&nbsp;This&nbsp;is&nbsp;item&nbsp;1</samp>
    <br><samp>-&nbsp;This&nbsp;is&nbsp;item&nbsp;2</samp>

    <p><samp>-&nbsp;Bullets&nbsp;are&nbsp;"-",&nbsp;"*"&nbsp;or&nbsp;"+".</samp>
    <br><samp>&nbsp;&nbsp;Continuing&nbsp;text&nbsp;must&nbsp;be&nbsp;aligned</samp>
    <br><samp>&nbsp;&nbsp;after&nbsp;the&nbsp;bullet&nbsp;and&nbsp;whitespace.</samp>

    <p><samp>Note&nbsp;that&nbsp;a&nbsp;blank&nbsp;line&nbsp;is&nbsp;required</samp>
    <br><samp>before&nbsp;the&nbsp;first&nbsp;item&nbsp;and&nbsp;after&nbsp;the</samp>
    <br><samp>last,&nbsp;but&nbsp;is&nbsp;optional&nbsp;between&nbsp;items.</samp>
        <td>Bullet lists:
            <ul>
            <li>This is item 1
            <li>This is item 2
            <li>Bullets are "-", "*" or "+".
            Continuing text must be aligned
            after the bullet and whitespace.
            </ul>
            <p>Note that a blank line is required before the first
            item and after the last, but is optional between items.
        </table>

        <h2><a href="#contents" name="enumerated-lists" class="backref"
            >Enumerated Lists</a></h2>

        <p>(<a href="http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#enumerated-lists">details</a>)

        <p><table border="1" width="100%" bgcolor="#ffffcc" cellpadding="3">
        <thead>
        <tr align="left" bgcolor="#99CCFF">
        <th width="50%">Plain text
        <th width="50%">Typical result
        </thead>
        <tbody>
        <tr valign="top">
        <td>
    <samp>Enumerated&nbsp;lists:</samp>

    <p><samp>3.&nbsp;This&nbsp;is&nbsp;the&nbsp;first&nbsp;item</samp>
    <br><samp>4.&nbsp;This&nbsp;is&nbsp;the&nbsp;second&nbsp;item</samp>
    <br><samp>5.&nbsp;Enumerators&nbsp;are&nbsp;arabic&nbsp;numbers,</samp>
    <br><samp>&nbsp;&nbsp;&nbsp;single&nbsp;letters,&nbsp;or&nbsp;roman&nbsp;numerals</samp>
    <br><samp>6.&nbsp;List&nbsp;items&nbsp;should&nbsp;be&nbsp;sequentially</samp>
    <br><samp>&nbsp;&nbsp;&nbsp;numbered,&nbsp;but&nbsp;need&nbsp;not&nbsp;start&nbsp;at&nbsp;1</samp>
    <br><samp>&nbsp;&nbsp;&nbsp;(although&nbsp;not&nbsp;all&nbsp;formatters&nbsp;will</samp>
    <br><samp>&nbsp;&nbsp;&nbsp;honour&nbsp;the&nbsp;first&nbsp;index).</samp>
    <br><samp>#.&nbsp;This&nbsp;item&nbsp;is&nbsp;auto-enumerated</samp>
        <td>Enumerated lists:
            <ol type="1">
            <li value="3">This is the first item
            <li>This is the second item
            <li>Enumerators are arabic numbers, single letters,
            or roman numerals
            <li>List items should be sequentially numbered,
            but need not start at 1 (although not all
            formatters will honour the first index).
            <li>This item is auto-enumerated
            </ol>
        </table>

        <h2><a href="#contents" name="definition-lists" class="backref"
            >Definition Lists</a></h2>

        <p>(<a href="http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#definition-lists">details</a>)

        <p><table border="1" width="100%" bgcolor="#ffffcc" cellpadding="3">
        <thead>
        <tr align="left" bgcolor="#99CCFF">
        <th width="50%">Plain text
        <th width="50%">Typical result
        </thead>
        <tbody>
        <tr valign="top">
        <td>
    <samp>Definition&nbsp;lists:</samp>
    <br>
    <br><samp>what</samp>
    <br><samp>&nbsp;&nbsp;Definition&nbsp;lists&nbsp;associate&nbsp;a&nbsp;term&nbsp;with</samp>
    <br><samp>&nbsp;&nbsp;a&nbsp;definition.</samp>
    <br>
    <br><samp>how</samp>
    <br><samp>&nbsp;&nbsp;The&nbsp;term&nbsp;is&nbsp;a&nbsp;one-line&nbsp;phrase,&nbsp;and&nbsp;the</samp>
    <br><samp>&nbsp;&nbsp;definition&nbsp;is&nbsp;one&nbsp;or&nbsp;more&nbsp;paragraphs&nbsp;or</samp>
    <br><samp>&nbsp;&nbsp;body&nbsp;elements,&nbsp;indented&nbsp;relative&nbsp;to&nbsp;the</samp>
    <br><samp>&nbsp;&nbsp;term.&nbsp;Blank&nbsp;lines&nbsp;are&nbsp;not&nbsp;allowed</samp>
    <br><samp>&nbsp;&nbsp;between&nbsp;term&nbsp;and&nbsp;definition.</samp>
        <td>Definition lists:
            <dl>
            <dt><strong>what</strong>
            <dd>Definition lists associate a term with
            a definition.

            <dt><strong>how</strong>
            <dd>The term is a one-line phrase, and the
            definition is one or more paragraphs or
            body elements, indented relative to the
            term.  Blank lines are not allowed
            between term and definition.
            </dl>
        </table>

        <h2><a href="#contents" name="field-lists" class="backref"
            >Field Lists</a></h2>

        <p>(<a href="http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#field-lists">details</a>)

        <p><table border="1" width="100%" bgcolor="#ffffcc" cellpadding="3">
        <thead>
        <tr align="left" bgcolor="#99CCFF">
        <th width="50%">Plain text
        <th width="50%">Typical result
        </thead>
        <tbody>
        <tr valign="top">
        <td>
    <samp>:Authors:</samp>
    <br><samp>&nbsp;&nbsp;&nbsp;&nbsp;Tony&nbsp;J.&nbsp;(Tibs)&nbsp;Ibbs,</samp>
    <br><samp>&nbsp;&nbsp;&nbsp;&nbsp;David&nbsp;Goodger</samp>

    <p><samp>&nbsp;&nbsp;&nbsp;&nbsp;(and&nbsp;sundry&nbsp;other&nbsp;good-natured&nbsp;folks)</samp>

    <p><samp>:Version:&nbsp;1.0&nbsp;of&nbsp;2001/08/08</samp>
    <br><samp>:Dedication:&nbsp;To&nbsp;my&nbsp;father.</samp>
        <td>
            <table>
            <tr valign="top">
            <td><strong>Authors:</strong>
            <td>Tony J. (Tibs) Ibbs,
            David Goodger
            <tr><td><td>(and sundry other good-natured folks)
            <tr><td><strong>Version:</strong><td>1.0 of 2001/08/08
            <tr><td><strong>Dedication:</strong><td>To my father.
            </table>
        </table>

        <p>Field lists are used as part of an extension syntax, such as
        options for <a href="#directives">directives</a>, or database-like
        records meant for further processing.  Field lists may also be
        used as generic two-column table constructs in documents.

        <h2><a href="#contents" name="option-lists" class="backref"
            >Option Lists</a></h2>

        <p>(<a href="http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#option-lists">details</a>)

        <p><table border="1" width="100%" bgcolor="#ffffcc" cellpadding="3">
        <thead>
        <tr align="left" bgcolor="#99CCFF">
        <th width="50%">Plain text
        <th width="50%">Typical result
        </thead>
        <tbody>
        <tr valign="top">
        <td>
            <p><samp>
    -a&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;command-line&nbsp;option&nbsp;"a"
    <br>-b&nbsp;file&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;options&nbsp;can&nbsp;have&nbsp;arguments
    <br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;and&nbsp;long&nbsp;descriptions
    <br>--long&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;options&nbsp;can&nbsp;be&nbsp;long&nbsp;also
    <br>--input=file&nbsp;&nbsp;long&nbsp;options&nbsp;can&nbsp;also&nbsp;have
    <br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;arguments
    <br>/V&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;DOS/VMS-style&nbsp;options&nbsp;too
    </samp>

        <td>
            <table border="0" width="100%">
            <tbody valign="top">
                <tr>
                <td width="30%"><samp>-a</samp>
                <td>command-line option "a"
                <tr>
                <td><samp>-b <i>file</i></samp>
                <td>options can have arguments and long descriptions
                <tr>
                <td><samp>--long</samp>
                <td>options can be long also
                <tr>
                <td><samp>--input=<i>file</i></samp>
                <td>long options can also have arguments
                <tr>
                <td><samp>/V</samp>
                <td>DOS/VMS-style options too
            </table>
        </table>

        <p>There must be at least two spaces between the option and the
        description.

        <h2><a href="#contents" name="literal-blocks" class="backref"
            >Literal Blocks</a></h2>

        <p>(<a href="http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#literal-blocks">details</a>)

        <p><table border="1" width="100%" bgcolor="#ffffcc" cellpadding="3">
        <thead>
        <tr align="left" bgcolor="#99CCFF">
        <th width="50%">Plain text
        <th width="50%">Typical result
        </thead>
        <tbody>
        <tr valign="top">
        <td>
    <samp>A&nbsp;paragraph&nbsp;containing&nbsp;only&nbsp;two&nbsp;colons</samp>
    <br><samp>indicates&nbsp;that&nbsp;the&nbsp;following&nbsp;indented</samp>
    <br><samp>or&nbsp;quoted&nbsp;text&nbsp;is&nbsp;a&nbsp;literal&nbsp;block.</samp>
    <br>
    <br><samp>::</samp>
    <br>
    <br><samp>&nbsp;&nbsp;Whitespace,&nbsp;newlines,&nbsp;blank&nbsp;lines,&nbsp;and</samp>
    <br><samp>&nbsp;&nbsp;all&nbsp;kinds&nbsp;of&nbsp;markup&nbsp;(like&nbsp;*this*&nbsp;or</samp>
    <br><samp>&nbsp;&nbsp;\this)&nbsp;is&nbsp;preserved&nbsp;by&nbsp;literal&nbsp;blocks.</samp>
    <br>
    <br><samp>&nbsp;&nbsp;The&nbsp;paragraph&nbsp;containing&nbsp;only&nbsp;'::'</samp>
    <br><samp>&nbsp;&nbsp;will&nbsp;be&nbsp;omitted&nbsp;from&nbsp;the&nbsp;result.</samp>
    <br>
    <br><samp>The&nbsp;``::``&nbsp;may&nbsp;be&nbsp;tacked&nbsp;onto&nbsp;the&nbsp;very</samp>
    <br><samp>end&nbsp;of&nbsp;any&nbsp;paragraph.&nbsp;The&nbsp;``::``&nbsp;will&nbsp;be</samp>
    <br><samp>omitted&nbsp;if&nbsp;it&nbsp;is&nbsp;preceded&nbsp;by&nbsp;whitespace.</samp>
    <br><samp>The&nbsp;``::``&nbsp;will&nbsp;be&nbsp;converted&nbsp;to&nbsp;a&nbsp;single</samp>
    <br><samp>colon&nbsp;if&nbsp;preceded&nbsp;by&nbsp;text,&nbsp;like&nbsp;this::</samp>
    <br>
    <br><samp>&nbsp;&nbsp;It's&nbsp;very&nbsp;convenient&nbsp;to&nbsp;use&nbsp;this&nbsp;form.</samp>
    <br>
    <br><samp>Literal&nbsp;blocks&nbsp;end&nbsp;when&nbsp;text&nbsp;returns&nbsp;to</samp>
    <br><samp>the&nbsp;preceding&nbsp;paragraph's&nbsp;indentation.</samp>
    <br><samp>This&nbsp;means&nbsp;that&nbsp;something&nbsp;like&nbsp;this</samp>
    <br><samp>is&nbsp;possible::</samp>
    <br>
    <br><samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;We&nbsp;start&nbsp;here</samp>
    <br><samp>&nbsp;&nbsp;&nbsp;&nbsp;and&nbsp;continue&nbsp;here</samp>
    <br><samp>&nbsp;&nbsp;and&nbsp;end&nbsp;here.</samp>
    <br>
    <br><samp>Per-line&nbsp;quoting&nbsp;can&nbsp;also&nbsp;be&nbsp;used&nbsp;on</samp>
    <br><samp>unindented&nbsp;literal&nbsp;blocks::</samp>
    <br>
    <br><samp>&gt;&nbsp;Useful&nbsp;for&nbsp;quotes&nbsp;from&nbsp;email&nbsp;and</samp>
    <br><samp>&gt;&nbsp;for&nbsp;Haskell&nbsp;literate&nbsp;programming.</samp>

        <td>
            <p>A paragraph containing only two colons
    indicates that the following indented or quoted
    text is a literal block.

            <pre>
    Whitespace, newlines, blank lines, and
    all kinds of markup (like *this* or
    \this) is preserved by literal blocks.

    The paragraph containing only '::'
    will be omitted from the result.</pre>

            <p>The <samp>::</samp> may be tacked onto the very
    end of any paragraph. The <samp>::</samp> will be
    omitted if it is preceded by whitespace.
    The <samp>::</samp> will be converted to a single
    colon if preceded by text, like this:

            <pre>
    It's very convenient to use this form.</pre>

            <p>Literal blocks end when text returns to
    the preceding paragraph's indentation.
    This means that something like this is possible:

            <pre>
        We start here
        and continue here
    and end here.</pre>

            <p>Per-line quoting can also be used on
    unindented literal blocks:

            <pre>
    &gt; Useful for quotes from email and
    &gt; for Haskell literate programming.</pre>
        </table>

        <h2><a href="#contents" name="line-blocks" class="backref"
            >Line Blocks</a></h2>

        <p>(<a href="http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#line-blocks">details</a>)

        <p><table border="1" width="100%" bgcolor="#ffffcc" cellpadding="3">
        <thead>
        <tr align="left" bgcolor="#99CCFF">
        <th width="50%">Plain text
        <th width="50%">Typical result
        </thead>
        <tbody>
        <tr valign="top">
        <td>
    <samp>|&nbsp;Line&nbsp;blocks&nbsp;are&nbsp;useful&nbsp;for&nbsp;addresses,</samp>
    <br><samp>|&nbsp;verse,&nbsp;and&nbsp;adornment-free&nbsp;lists.</samp>
    <br><samp>|</samp>
    <br><samp>|&nbsp;Each&nbsp;new&nbsp;line&nbsp;begins&nbsp;with&nbsp;a</samp>
    <br><samp>|&nbsp;vertical&nbsp;bar&nbsp;("|").</samp>
    <br><samp>|&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Line&nbsp;breaks&nbsp;and&nbsp;initial&nbsp;indents</samp>
    <br><samp>|&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;are&nbsp;preserved.</samp>
    <br><samp>|&nbsp;Continuation&nbsp;lines&nbsp;are&nbsp;wrapped</samp>
    <br><samp>&nbsp;&nbsp;portions&nbsp;of&nbsp;long&nbsp;lines;&nbsp;they&nbsp;begin</samp>
    <br><samp>&nbsp;&nbsp;with&nbsp;spaces&nbsp;in&nbsp;place&nbsp;of&nbsp;vertical&nbsp;bars.</samp>

        <td>
            <div class="line-block">
            <div class="line">Line blocks are useful for addresses,</div>
            <div class="line">verse, and adornment-free lists.</div>
            <div class="line"><br /></div>
            <div class="line">Each new line begins with a</div>
            <div class="line">vertical bar ("|").</div>
            <div class="line-block">
                <div class="line">Line breaks and initial indents</div>
                <div class="line">are preserved.</div>
            </div>
            <div class="line">Continuation lines are wrapped portions
                of long lines; they begin
                with spaces in place of vertical bars.</div>
            </div>
        </table>

        <h2><a href="#contents" name="block-quotes" class="backref"
            >Block Quotes</a></h2>

        <p>(<a href="http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#block-quotes">details</a>)

        <p><table border="1" width="100%" bgcolor="#ffffcc" cellpadding="3">
        <thead>
        <tr align="left" bgcolor="#99CCFF">
        <th width="50%">Plain text
        <th width="50%">Typical result
        </thead>
        <tbody>
        <tr valign="top">
        <td>
    <samp>Block&nbsp;quotes&nbsp;are&nbsp;just:</samp>

    <p><samp>&nbsp;&nbsp;&nbsp;&nbsp;Indented&nbsp;paragraphs,</samp>

    <p><samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;and&nbsp;they&nbsp;may&nbsp;nest.</samp>
        <td>
            Block quotes are just:
            <blockquote>
            <p>Indented paragraphs,
            <blockquote>
            <p>and they may nest.
            </blockquote>
            </blockquote>
        </table>

        <p>Use <a href="#comments">empty comments</a> to separate indentation
        contexts, such as block quotes and directive contents.</p>

        <h2><a href="#contents" name="doctest-blocks" class="backref"
            >Doctest Blocks</a></h2>

        <p>(<a href="http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#doctest-blocks">details</a>)

        <p><table border="1" width="100%" bgcolor="#ffffcc" cellpadding="3">
        <thead>
        <tr align="left" bgcolor="#99CCFF">
        <th width="50%">Plain text
        <th width="50%">Typical result
        </thead>
        <tbody>
        <tr valign="top">
        <td>
            <p><samp>Doctest&nbsp;blocks&nbsp;are&nbsp;interactive
    <br>Python&nbsp;sessions.&nbsp;They&nbsp;begin&nbsp;with
    <br>"``&gt;&gt;&gt;``"&nbsp;and&nbsp;end&nbsp;with&nbsp;a&nbsp;blank&nbsp;line.</samp>

            <p><samp>&gt;&gt;&gt;&nbsp;print&nbsp;"This&nbsp;is&nbsp;a&nbsp;doctest&nbsp;block."
    <br>This&nbsp;is&nbsp;a&nbsp;doctest&nbsp;block.</samp>

        <td>
            <p>Doctest blocks are interactive
            Python sessions. They begin with
            "<samp>&gt;&gt;&gt;</samp>" and end with a blank line.

            <p><samp>&gt;&gt;&gt;&nbsp;print&nbsp;"This&nbsp;is&nbsp;a&nbsp;doctest&nbsp;block."
    <br>This&nbsp;is&nbsp;a&nbsp;doctest&nbsp;block.</samp>
        </table>

        <p>"The <a
        href="http://www.python.org/doc/current/lib/module-doctest.html">doctest</a>
        module searches a module's docstrings for text that looks like an
        interactive Python session, then executes all such sessions to
        verify they still work exactly as shown." (From the doctest docs.)

        <h2><a href="#contents" name="tables" class="backref"
            >Tables</a></h2>

        <p>(<a href="http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#tables">details</a>)

        <p>There are two syntaxes for tables in reStructuredText.  Grid
        tables are complete but cumbersome to create.  Simple tables are
        easy to create but limited (no row spans, etc.).</p>

        <p><table border="1" width="100%" bgcolor="#ffffcc" cellpadding="3">
        <thead>
        <tr align="left" bgcolor="#99CCFF">
        <th width="50%">Plain text
        <th width="50%">Typical result
        </thead>
        <tbody>
        <tr valign="top">
        <td>
    <p><samp>Grid table:</samp></p>

    <p><samp>+------------+------------+-----------+</samp>
    <br><samp>|&nbsp;Header&nbsp;1&nbsp;&nbsp;&nbsp;|&nbsp;Header&nbsp;2&nbsp;&nbsp;&nbsp;|&nbsp;Header&nbsp;3&nbsp;&nbsp;|</samp>
    <br><samp>+============+============+===========+</samp>
    <br><samp>|&nbsp;body&nbsp;row&nbsp;1&nbsp;|&nbsp;column&nbsp;2&nbsp;&nbsp;&nbsp;|&nbsp;column&nbsp;3&nbsp;&nbsp;|</samp>
    <br><samp>+------------+------------+-----------+</samp>
    <br><samp>|&nbsp;body&nbsp;row&nbsp;2&nbsp;|&nbsp;Cells&nbsp;may&nbsp;span&nbsp;columns.|</samp>
    <br><samp>+------------+------------+-----------+</samp>
    <br><samp>|&nbsp;body&nbsp;row&nbsp;3&nbsp;|&nbsp;Cells&nbsp;may&nbsp;&nbsp;|&nbsp;-&nbsp;Cells&nbsp;&nbsp;&nbsp;|</samp>
    <br><samp>+------------+&nbsp;span&nbsp;rows.&nbsp;|&nbsp;-&nbsp;contain&nbsp;|</samp>
    <br><samp>|&nbsp;body&nbsp;row&nbsp;4&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;-&nbsp;blocks.&nbsp;|</samp>
    <br><samp>+------------+------------+-----------+</samp></p>
        <td>
            <p>Grid table:</p>
            <table border="1">
            <thead valign="bottom">
                <tr>
                <th>Header 1
                <th>Header 2
                <th>Header 3
                </tr>
            </thead>
            <tbody valign="top">
                <tr>
                <td>body row 1
                <td>column 2
                <td>column 3
                </tr>
                <tr>
                <td>body row 2
                <td colspan="2">Cells may span columns.
                </tr>
                <tr>
                <td>body row 3
                <td rowspan="2">Cells may<br>span rows.
                <td rowspan="2">
                    <ul>
                    <li>Cells
                    <li>contain
                    <li>blocks.
                    </ul>
                </tr>
                <tr>
                <td>body row 4
                </tr>
            </table>
        <tr valign="top">
        <td>
    <p><samp>Simple table:</samp></p>

    <p><samp>=====&nbsp;&nbsp;=====&nbsp;&nbsp;======</samp>
    <br><samp>&nbsp;&nbsp;&nbsp;Inputs&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Output</samp>
    <br><samp>------------&nbsp;&nbsp;------</samp>
    <br><samp>&nbsp;&nbsp;A&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;B&nbsp;&nbsp;&nbsp;&nbsp;A&nbsp;or&nbsp;B</samp>
    <br><samp>=====&nbsp;&nbsp;=====&nbsp;&nbsp;======</samp>
    <br><samp>False&nbsp;&nbsp;False&nbsp;&nbsp;False</samp>
    <br><samp>True&nbsp;&nbsp;&nbsp;False&nbsp;&nbsp;True</samp>
    <br><samp>False&nbsp;&nbsp;True&nbsp;&nbsp;&nbsp;True</samp>
    <br><samp>True&nbsp;&nbsp;&nbsp;True&nbsp;&nbsp;&nbsp;True</samp>
    <br><samp>=====&nbsp;&nbsp;=====&nbsp;&nbsp;======</samp></p>

        <td>
            <p>Simple table:</p>
            <table border="1">
            <colgroup>
                <col width="31%">
                <col width="31%">
                <col width="38%">
            </colgroup>
            <thead valign="bottom">
                <tr>
                <th colspan="2">Inputs
                <th>Output
                <tr>
                <th>A
                <th>B
                <th>A or B
            <tbody valign="top">
                <tr>
                <td>False
                <td>False
                <td>False
                <tr>
                <td>True
                <td>False
                <td>True
                <tr>
                <td>False
                <td>True
                <td>True
                <tr>
                <td>True
                <td>True
                <td>True
            </table>

        </table>

        <h2><a href="#contents" name="transitions" class="backref"
            >Transitions</a></h2>

        <p>(<a href="http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#transitions">details</a>)

        <p><table border="1" width="100%" bgcolor="#ffffcc" cellpadding="3">
        <thead>
        <tr align="left" bgcolor="#99CCFF">
        <th width="50%">Plain text
        <th width="50%">Typical result
        </thead>
        <tbody>
        <tr valign="top">
        <td>
            <p><samp>
    A&nbsp;transition&nbsp;marker&nbsp;is&nbsp;a&nbsp;horizontal&nbsp;line
    <br>of&nbsp;4&nbsp;or&nbsp;more&nbsp;repeated&nbsp;punctuation
    <br>characters.</samp>

            <p><samp>------------</samp>

            <p><samp>A&nbsp;transition&nbsp;should&nbsp;not&nbsp;begin&nbsp;or&nbsp;end&nbsp;a
    <br>section&nbsp;or&nbsp;document,&nbsp;nor&nbsp;should&nbsp;two
    <br>transitions&nbsp;be&nbsp;immediately&nbsp;adjacent.</samp>

        <td>
            <p>A transition marker is a horizontal line
            of 4 or more repeated punctuation
            characters.</p>

            <hr>

            <p>A transition should not begin or end a
            section or document, nor should two
            transitions be immediately adjacent.
        </table>

        <p>Transitions are commonly seen in novels and short fiction, as a
        gap spanning one or more lines, marking text divisions or
        signaling changes in subject, time, point of view, or emphasis.

        <h2><a href="#contents" name="explicit-markup" class="backref"
            >Explicit Markup</a></h2>

        <p>Explicit markup blocks are used for constructs which float
        (footnotes), have no direct paper-document representation
        (hyperlink targets, comments), or require specialized processing
        (directives).  They all begin with two periods and whitespace, the
        "explicit markup start".

        <h3><a href="#contents" name="footnotes" class="backref"
            >Footnotes</a></h3>

        <p>(<a href="http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#footnotes">details</a>)

        <p><table border="1" width="100%" bgcolor="#ffffcc" cellpadding="3">
        <thead>
        <tr align="left" bgcolor="#99CCFF">
        <th width="50%">Plain text
        <th width="50%">Typical result
        </thead>
        <tbody>

        <tr valign="top">
        <td>
            <samp>Footnote&nbsp;references,&nbsp;like&nbsp;[5]_.</samp>
            <br><samp>Note&nbsp;that&nbsp;footnotes&nbsp;may&nbsp;get</samp>
            <br><samp>rearranged,&nbsp;e.g.,&nbsp;to&nbsp;the&nbsp;bottom&nbsp;of</samp>
            <br><samp>the&nbsp;"page".</samp>

            <p><samp>..&nbsp;[5]&nbsp;A&nbsp;numerical&nbsp;footnote.&nbsp;Note</samp>
            <br><samp>&nbsp;&nbsp;&nbsp;there's&nbsp;no&nbsp;colon&nbsp;after&nbsp;the&nbsp;``]``.</samp>

        <td>
            Footnote references, like <sup><a href="#5">5</a></sup>.
            Note that footnotes may get rearranged, e.g., to the bottom of
            the "page".

            <p><table>
            <tr><td colspan="2"><hr>
            <!-- <tr><td colspan="2">Footnotes: -->
            <tr><td><a name="5"><strong>[5]</strong></a><td> A numerical footnote.
            Note there's no colon after the <samp>]</samp>.
            </table>

        <tr valign="top">
        <td>
            <samp>Autonumbered&nbsp;footnotes&nbsp;are</samp>
            <br><samp>possible,&nbsp;like&nbsp;using&nbsp;[#]_&nbsp;and&nbsp;[#]_.</samp>
            <p><samp>..&nbsp;[#]&nbsp;This&nbsp;is&nbsp;the&nbsp;first&nbsp;one.</samp>
            <br><samp>..&nbsp;[#]&nbsp;This&nbsp;is&nbsp;the&nbsp;second&nbsp;one.</samp>

            <p><samp>They&nbsp;may&nbsp;be&nbsp;assigned&nbsp;'autonumber</samp>
            <br><samp>labels'&nbsp;-&nbsp;for&nbsp;instance,
            <br>[#fourth]_&nbsp;and&nbsp;[#third]_.</samp>

            <p><samp>..&nbsp;[#third]&nbsp;a.k.a.&nbsp;third_</samp>
            <p><samp>..&nbsp;[#fourth]&nbsp;a.k.a.&nbsp;fourth_</samp>
        <td>
            Autonumbered footnotes are possible, like using <sup><a
            href="#auto1">1</a></sup> and <sup><a href="#auto2">2</a></sup>.

            <p>They may be assigned 'autonumber labels' - for instance,
            <sup><a href="#fourth">4</a></sup> and <sup><a
            href="#third">3</a></sup>.

            <p><table>
            <tr><td colspan="2"><hr>
            <!-- <tr><td colspan="2">Footnotes: -->
            <tr><td><a name="auto1"><strong>[1]</strong></a><td> This is the first one.
            <tr><td><a name="auto2"><strong>[2]</strong></a><td> This is the second one.
            <tr><td><a name="third"><strong>[3]</strong></a><td> a.k.a. <a href="#third">third</a>
            <tr><td><a name="fourth"><strong>[4]</strong></a><td> a.k.a. <a href="#fourth">fourth</a>
            </table>

        <tr valign="top">
        <td>
            <samp>Auto-symbol&nbsp;footnotes&nbsp;are&nbsp;also</samp>
            <br><samp>possible,&nbsp;like&nbsp;this:&nbsp;[*]_&nbsp;and&nbsp;[*]_.</samp>
            <p><samp>..&nbsp;[*]&nbsp;This&nbsp;is&nbsp;the&nbsp;first&nbsp;one.</samp>
            <br><samp>..&nbsp;[*]&nbsp;This&nbsp;is&nbsp;the&nbsp;second&nbsp;one.</samp>

        <td>
            Auto-symbol footnotes are also
            possible, like this: <sup><a href="#symbol1">*</a></sup>
            and <sup><a href="#symbol2">&dagger;</a></sup>.

            <p><table>
            <tr><td colspan="2"><hr>
            <!-- <tr><td colspan="2">Footnotes: -->
            <tr><td><a name="symbol1"><strong>[*]</strong></a><td> This is the first symbol footnote
            <tr><td><a name="symbol2"><strong>[&dagger;]</strong></a><td> This is the second one.
            </table>

        </table>

        <p>The numbering of auto-numbered footnotes is determined by the
        order of the footnotes, not of the references. For auto-numbered
        footnote references without autonumber labels
        ("<samp>[#]_</samp>"), the references and footnotes must be in the
        same relative order. Similarly for auto-symbol footnotes
        ("<samp>[*]_</samp>").

        <h3><a href="#contents" name="citations" class="backref"
            >Citations</a></h3>

        <p>(<a href="http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#citations">details</a>)

        <p><table border="1" width="100%" bgcolor="#ffffcc" cellpadding="3">
        <thead>
        <tr align="left" bgcolor="#99CCFF">
        <th width="50%">Plain text
        <th width="50%">Typical result
        </thead>
        <tbody>

        <tr valign="top">
        <td>
            <samp>Citation&nbsp;references,&nbsp;like&nbsp;[CIT2002]_.</samp>
            <br><samp>Note&nbsp;that&nbsp;citations&nbsp;may&nbsp;get</samp>
            <br><samp>rearranged,&nbsp;e.g.,&nbsp;to&nbsp;the&nbsp;bottom&nbsp;of</samp>
            <br><samp>the&nbsp;"page".</samp>

            <p><samp>..&nbsp;[CIT2002]&nbsp;A&nbsp;citation</samp>
            <br><samp>&nbsp;&nbsp;&nbsp;(as&nbsp;often&nbsp;used&nbsp;in&nbsp;journals).</samp>

            <p><samp>Citation&nbsp;labels&nbsp;contain&nbsp;alphanumerics,</samp>
            <br><samp>underlines,&nbsp;hyphens&nbsp;and&nbsp;fullstops.</samp>
            <br><samp>Case&nbsp;is&nbsp;not&nbsp;significant.</samp>

            <p><samp>Given&nbsp;a&nbsp;citation&nbsp;like&nbsp;[this]_,&nbsp;one</samp>
            <br><samp>can&nbsp;also&nbsp;refer&nbsp;to&nbsp;it&nbsp;like&nbsp;this_.</samp>

            <p><samp>..&nbsp;[this]&nbsp;here.</samp>

        <td>
            Citation references, like <a href="#cit2002">[CIT2002]</a>.
            Note that citations may get rearranged, e.g., to the bottom of
            the "page".

            <p>Citation labels contain alphanumerics, underlines, hyphens
            and fullstops.  Case is not significant.

            <p>Given a citation like <a href="#this">[this]</a>, one
            can also refer to it like <a href="#this">this</a>.

            <p><table>
            <tr><td colspan="2"><hr>
            <!-- <tr><td colspan="2">Citations: -->
            <tr><td><a name="cit2002"><strong>[CIT2002]</strong></a><td> A citation
            (as often used in journals).
            <tr><td><a name="this"><strong>[this]</strong></a><td> here.
            </table>

        </table>

        <h3><a href="#contents" name="hyperlink-targets" class="backref"
            >Hyperlink Targets</a></h3>

        <p>(<a href="http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#hyperlink-targets">details</a>)

        <h4><a href="#contents" name="external-hyperlink-targets" class="backref"
            >External Hyperlink Targets</a></h4>

        <p><table border="1" width="100%" bgcolor="#ffffcc" cellpadding="3">
        <thead>
        <tr align="left" bgcolor="#99CCFF">
        <th width="50%">Plain text
        <th width="50%">Typical result
        </thead>
        <tbody>

        <tr valign="top">
        <td rowspan="2">
            <samp>External&nbsp;hyperlinks,&nbsp;like&nbsp;Python_.</samp>

            <p><samp>..&nbsp;_Python:&nbsp;http://www.python.org/</samp>
        <td>
            <table width="100%">
            <tr bgcolor="#99CCFF"><td><em>Fold-in form</em>
            <tr><td>External hyperlinks, like
            <a href="http://www.python.org/">Python</a>.
            </table>
        <tr valign="top">
        <td>
            <table width="100%">
            <tr bgcolor="#99CCFF"><td><em>Call-out form</em>
            <tr><td>External hyperlinks, like
            <a href="#labPython"><i>Python</i></a>.

            <p><table>
                <tr><td colspan="2"><hr>
                <tr><td><a name="labPython"><i>Python:</i></a>
                <td> <a href="http://www.python.org/">http://www.python.org/</a>
            </table>
            </table>
        </table>

        <p>"<em>Fold-in</em>" is the representation typically used in HTML
        documents (think of the indirect hyperlink being "folded in" like
        ingredients into a cake), and "<em>call-out</em>" is more suitable for
        printed documents, where the link needs to be presented explicitly, for
        example as a footnote.  You can force usage of the call-out form by
        using the
        "<a href="http://docutils.sourceforge.net/docs/ref/rst/directives.html#target-notes">target-notes</a>"
        directive.

        <p>reStructuredText also provides for <b>embedded URIs</b> (<a
        href="http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#embedded-uris">details</a>),
        a convenience at the expense of readability.  A hyperlink
        reference may directly embed a target URI inline, within angle
        brackets.  The following is exactly equivalent to the example above:

        <p><table border="1" width="100%" bgcolor="#ffffcc" cellpadding="3">
        <thead>
        <tr align="left" bgcolor="#99CCFF">
        <th width="50%">Plain text
        <th width="50%">Typical result
        </thead>
        <tbody>

        <tr valign="top">
        <td rowspan="2">
            <samp>External&nbsp;hyperlinks,&nbsp;like&nbsp;`Python
    <br>&lt;http://www.python.org/&gt;`_.</samp>
        <td>External hyperlinks, like
            <a href="http://www.python.org/">Python</a>.
        </table>

        <h4><a href="#contents" name="internal-hyperlink-targets" class="backref"
            >Internal Hyperlink Targets</a></h4>

        <p><table border="1" width="100%" bgcolor="#ffffcc" cellpadding="3">
        <thead>
        <tr align="left" bgcolor="#99CCFF">
        <th width="50%">Plain text
        <th width="50%">Typical result
        </thead>
        <tbody>

        <tr valign="top">
        <td rowspan="2"><samp>Internal&nbsp;crossreferences,&nbsp;like&nbsp;example_.</samp>

            <p><samp>..&nbsp;_example:</samp>

            <p><samp>This&nbsp;is&nbsp;an&nbsp;example&nbsp;crossreference&nbsp;target.</samp>
        <td>
            <table width="100%">
            <tr bgcolor="#99CCFF"><td><em>Fold-in form</em>
            <!-- Note that some browsers may not like an "a" tag that -->
            <!-- does not have any content, so we could arbitrarily   -->
            <!-- use the first word as content - *or* just trust to   -->
            <!-- luck!                                                -->
            <tr><td>Internal crossreferences, like <a href="#example-foldin">example</a>
            <p><a name="example-foldin">This</a> is an example
                crossreference target.
            </table>
        <tr valign="top">
        <td>
            <table width="100%">
            <tr><td bgcolor="#99CCFF"><em>Call-out form</em>
            <tr><td>Internal crossreferences, like <a href="#example-callout">example</a>

            <p><a name="example-callout"><i>example:</i></a>
                <br>This is an example crossreference target.
            </table>

        </table>

        <h4><a href="#contents" name="indirect-hyperlink-targets" class="backref"
            >Indirect Hyperlink Targets</a></h4>

        <p>(<a href="http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#indirect-hyperlink-targets">details</a>)

        <p><table border="1" width="100%" bgcolor="#ffffcc" cellpadding="3">
        <thead>
        <tr align="left" bgcolor="#99CCFF">
        <th width="50%">Plain text
        <th width="50%">Typical result
        </thead>
        <tbody>

        <tr valign="top">
        <td>
            <samp>Python_&nbsp;is&nbsp;`my&nbsp;favourite
    <br>programming&nbsp;language`__.</samp>

            <p><samp>..&nbsp;_Python:&nbsp;http://www.python.org/</samp>

            <p><samp>__&nbsp;Python_</samp>

        <td>
            <p><a href="http://www.python.org/">Python</a> is
            <a href="http://www.python.org/">my favourite
            programming language</a>.

        </table>

        <p>The second hyperlink target (the line beginning with
        "<samp>__</samp>") is both an indirect hyperlink target
        (<i>indirectly</i> pointing at the Python website via the
        "<samp>Python_</samp>" reference) and an <b>anonymous hyperlink
        target</b>. In the text, a double-underscore suffix is used to
        indicate an <b>anonymous hyperlink reference</b>.  In an anonymous
        hyperlink target, the reference text is not repeated.  This is
        useful for references with long text or throw-away references, but
        the target should be kept close to the reference to prevent them
        going out of sync.

        <h4><a href="#contents" name="implicit-hyperlink-targets" class="backref"
            >Implicit Hyperlink Targets</a></h4>

        <p>(<a href="http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#implicit-hyperlink-targets">details</a>)

        <p>Section titles, footnotes, and citations automatically generate
        hyperlink targets (the title text or footnote/citation label is
        used as the hyperlink name).

        <p><table border="1" width="100%" bgcolor="#ffffcc" cellpadding="3">
        <thead><tr align="left" bgcolor="#99CCFF">
        <th width="50%">Plain text
        <th width="50%">Typical result
        </thead>
        <tbody>

        <tr valign="top">
        <td>
            <samp>Titles&nbsp;are&nbsp;targets,&nbsp;too</samp>
            <br><samp>=======================</samp>
            <br><samp>Implict&nbsp;references,&nbsp;like&nbsp;`Titles&nbsp;are</samp>
            <br><samp>targets,&nbsp;too`_.</samp>
        <td>
            <font size="+2"><strong><a name="title">Titles are targets, too</a></strong></font>
            <p>Implict references, like <a href="#title">Titles are
            targets, too</a>.
        </table>

        <h3><a href="#contents" name="directives" class="backref"
            >Directives</a></h3>

        <p>(<a href="http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#directives">details</a>)

        <p>Directives are a general-purpose extension mechanism, a way of
        adding support for new constructs without adding new syntax.  For
        a description of all standard directives, see <a
        href="http://docutils.sourceforge.net/docs/ref/rst/directives.html" >reStructuredText
        Directives</a>.

        <p><table border="1" width="100%" bgcolor="#ffffcc" cellpadding="3">
        <thead>
        <tr align="left" bgcolor="#99CCFF">
        <th width="50%">Plain text
        <th width="50%">Typical result
        </thead>
        <tbody>
        <tr valign="top">
        <td><samp>For&nbsp;instance:</samp>

            <p><samp>..&nbsp;image::&nbsp;images/biohazard.png</samp>

        <td>
            For instance:
            <p><img src="/images/biohazard.png" alt="ball1">
        </table>

        <h3><a href="#contents" name="substitution-references-and-definitions"
            class="backref" >Substitution References and Definitions</a></h3>

        <p>(<a href="http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#substitution-definitions">details</a>)

        <p>Substitutions are like inline directives, allowing graphics and
        arbitrary constructs within text.

        <p><table border="1" width="100%" bgcolor="#ffffcc" cellpadding="3">
        <thead>
        <tr align="left" bgcolor="#99CCFF">
        <th width="50%">Plain text
        <th width="50%">Typical result
        </thead>
        <tbody>
        <tr valign="top">
        <td><samp>
    The&nbsp;|biohazard|&nbsp;symbol&nbsp;must&nbsp;be
    used&nbsp;on&nbsp;containers&nbsp;used&nbsp;to
    dispose&nbsp;of&nbsp;medical&nbsp;waste.</samp>

            <p><samp>
    ..&nbsp;|biohazard|&nbsp;image::&nbsp;biohazard.png</samp>

        <td>

            <p>The <img src="/images/biohazard.png" align="bottom" alt="biohazard"> symbol
            must be used on containers used to dispose of medical waste.

        </table>

        <h3><a href="#contents" name="comments" class="backref"
            >Comments</a></h3>

        <p>(<a href="http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#comments">details</a>)

        <p>Any text which begins with an explicit markup start but doesn't
        use the syntax of any of the constructs above, is a comment.

        <p><table border="1" width="100%" bgcolor="#ffffcc" cellpadding="3">
        <thead>
        <tr align="left" bgcolor="#99CCFF">
        <th width="50%">Plain text
        <th width="50%">Typical result
        </thead>
        <tbody>
        <tr valign="top">
        <td><samp>..&nbsp;This&nbsp;text&nbsp;will&nbsp;not&nbsp;be&nbsp;shown</samp>
            <br><samp>&nbsp;&nbsp;&nbsp;(but,&nbsp;for&nbsp;instance,&nbsp;in&nbsp;HTML&nbsp;might&nbsp;be</samp>
            <br><samp>&nbsp;&nbsp;&nbsp;rendered&nbsp;as&nbsp;an&nbsp;HTML&nbsp;comment)</samp>

        <td>&nbsp;
            <!-- This text will not be shown         -->
            <!-- (but, for instance in HTML might be -->
            <!-- rendered as an HTML comment)        -->

        <tr valign="top">
        <td>
            <samp>An&nbsp;"empty&nbsp;comment"&nbsp;does&nbsp;not</samp>
            <br><samp>consume&nbsp;following&nbsp;blocks.</samp>
            <br><samp>(An&nbsp;empty&nbsp;comment&nbsp;is&nbsp;".."&nbsp;with</samp>
            <br><samp>blank&nbsp;lines&nbsp;before&nbsp;and&nbsp;after.)</samp>
            <p><samp>..</samp>
            <p><samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;So&nbsp;this&nbsp;block&nbsp;is&nbsp;not&nbsp;"lost",</samp>
            <br><samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;despite&nbsp;its&nbsp;indentation.</samp>
        <td>
            An "empty comment" does not
            consume following blocks.
            (An empty comment is ".." with
            blank lines before and after.)
            <blockquote>
            So this block is not "lost",
            despite its indentation.
            </blockquote>
        </table>

        <h2><a href="#contents" name="getting-help" class="backref"
            >Getting Help</a></h2>

        <p>Users who have questions or need assistance with Docutils or
        reStructuredText should <a
        href="mailto:docutils-users@lists.sourceforge.net" >post a
        message</a> to the <a
        href="http://lists.sourceforge.net/lists/listinfo/docutils-users"
        >Docutils-Users mailing list</a>.  The <a
        href="http://docutils.sourceforge.net/" >Docutils project web
        site</a> has more information.

        <p><hr>
        <address>
        <p>Authors:
        <a href="http://www.tibsnjoan.co.uk/">Tibs</a>
        (<a href="mailto:tibs@tibsnjoan.co.uk"><tt>tibs@tibsnjoan.co.uk</tt></a>)
        and David Goodger
        (<a href="mailto:goodger@python.org">goodger@python.org</a>)
        </address>
        <!-- Created: Fri Aug 03 09:11:57 GMT Daylight Time 2001 -->
