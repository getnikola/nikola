#!/usr/bin/env python
"""Script to convert templates from Mako to Jinja2."""

import io
import glob
import sys
import os
import re
import json
import shutil
import tempfile

import colorama
import jinja2

dumb_replacements = [
    ["{% if any(post.is_mathjax for post in posts) %}", '{% if posts|selectattr("is_mathjax")|list %}'],
    ["json.dumps(title)", "title|tojson"],
    ["{{ parent.extra_head() }}", "{{ super() }}"],
    ["{{ parent.content() }}", "{{ super() }}"],
    ["prefix='\\", "prefix='"],
    ["og: http://ogp.me/ns# \\", "og: http://ogp.me/ns#"],
    ["article: http://ogp.me/ns/article# \\", "article: http://ogp.me/ns/article#"],
    ["fb: http://ogp.me/ns/fb# \\", "fb: http://ogp.me/ns/fb#"],
    ['dir="rtl" \\', 'dir="rtl"'],
    ['sorted(translations)', 'translations|sort'],
    ['abs(i - current_page)', '(i - current_page)|abs'],
]

dumber_replacements = [
    ['<%! import json %>\n\n', ''],
    ["<html\n\\", "<html\n"],
    ["\n'\\\n", "\n'\n"],
    ["{% endif %}\n\\", "{% endif %}\n"]
]


def jinjify(in_theme, out_theme):
    """Convert in_theme into a jinja version and put it in out_theme"""

    in_templates_path = os.path.join(in_theme, "templates")
    out_templates_path = os.path.join(out_theme, "templates")
    try:
        os.makedirs(out_templates_path)
    except Exception:
        pass
    lookup = jinja2.Environment()
    lookup.filters['tojson'] = json.dumps
    lookup.loader = jinja2.FileSystemLoader([out_templates_path], encoding='utf-8')
    for template in glob.glob(os.path.join(in_templates_path, "*.tmpl")):
        out_template = os.path.join(out_templates_path, os.path.basename(template))
        with io.open(template, "r", encoding="utf-8") as inf:
            data = mako2jinja(inf)

        lines = []
        for line in data.splitlines():
            for repl in dumb_replacements:
                line = line.replace(*repl)
            lines.append(line)
        data = '\n'.join(lines)

        for repl in dumber_replacements:
            data = data.replace(*repl)

        with io.open(out_template, "w+", encoding="utf-8") as outf:
            outf.write(data + '\n')

        # Syntax check output
        source, filename = lookup.loader.get_source(lookup, os.path.basename(template))[:2]
        try:
            lookup.parse(source)
        except Exception as e:
            error("Syntax error in {0}:{1}".format(out_template, e.lineno))

    parent = os.path.basename(in_theme.rstrip('/'))
    child = os.path.basename(out_theme.rstrip('/'))
    mappings = {
        'base-jinja': 'base',
        'bootstrap4-jinja': 'base-jinja',
    }

    if child in mappings:
        parent = mappings[child]

    # Copy assets in bootstrap/bootstrap4
    if child == 'bootstrap4-jinja':
        assets_dir = os.path.join(out_theme, "assets")
        if os.path.exists(assets_dir):
            shutil.rmtree(assets_dir)
        shutil.copytree(
            os.path.join(in_theme, "assets"), os.path.join(out_theme, "assets"),
            symlinks=True)

    # Copy bundles
    # shutil.copy(os.path.join(in_theme, "bundles"), os.path.join(out_theme, "bundles"))

    # Copy README
    if os.path.isfile(os.path.join(in_theme, "README.md")):
        shutil.copy(os.path.join(in_theme, "README.md"), os.path.join(out_theme, "README.md"))


def error(msg):
    print(colorama.Fore.RED + "ERROR:" + msg + colorama.Fore.RESET)


def mako2jinja(input_file):

    output = ''

    # TODO: OMG, this code is so horrible. Look at it; just look at it:

    macro_start = re.compile(r'(.*)<%\s*def name="([^"]*?)"\s*>(.*)', re.IGNORECASE)
    macro_end = re.compile(r'(.*)</%def>(.*)', re.IGNORECASE)

    if_start = re.compile(r'(.*)% *if (.*):(.*)', re.IGNORECASE)
    if_else = re.compile(r'(.*)% *else.*:(.*)', re.IGNORECASE)
    if_elif = re.compile(r'(.*)% *elif (.*):(.*)', re.IGNORECASE)
    if_end = re.compile(r'(.*)% *endif(.*)', re.IGNORECASE)

    for_start = re.compile(r'(.*)% *for (.*):(.*)', re.IGNORECASE)
    for_end = re.compile(r'(.*)% *endfor(.*)', re.IGNORECASE)

    namespace = re.compile(r'(.*)<% *namespace name="(.*?)".* file="(.*?)".*/>(.*)', re.IGNORECASE)
    inherit = re.compile(r'(.*)<% *inherit file="(.*?)".*/>(.*)', re.IGNORECASE)

    block_single_line = re.compile(r'(.*)<% *block.*name="(.*?)".*>(.*)</% *block>(.*)', re.IGNORECASE)
    block_start = re.compile(r'(.*)<% *block.*name="(.*?)".*>(.*)', re.IGNORECASE)
    block_end = re.compile(r'(.*)</%block>(.*)', re.IGNORECASE)

    val = re.compile(r'\$\{(.*?)\}', re.IGNORECASE)
    func_len = re.compile(r'len\((.*?)\)', re.IGNORECASE)
    filter_h = re.compile(r'\|h', re.IGNORECASE)
    filter_striphtml = re.compile(r'\|striphtml', re.IGNORECASE)
    filter_u = re.compile(r'\|u', re.IGNORECASE)

    comment_single_line = re.compile(r'^.*##(.*?)$', re.IGNORECASE)

    for line in input_file:

        # Process line for repeated inline replacements
        m_val = val.search(line)
        m_func_len = func_len.search(line)
        m_filter_h = filter_h.search(line)
        m_filter_striphtml = filter_striphtml.search(line)
        m_filter_u = filter_u.search(line)

        if m_val:
            line = val.sub(r'{{ \1 }}', line)

        if m_filter_h:
            line = filter_h.sub(r'|e', line)

        if m_filter_striphtml:
            line = filter_striphtml.sub(r'|e', line)

        if m_filter_u:
            line = filter_u.sub(r'|urlencode', line)

        if m_func_len:
            line = func_len.sub(r'\1|length', line)

        # Macro start/end
        m_macro_start = macro_start.search(line)
        if m_macro_start:
            line = m_macro_start.expand(r'\1{% macro \2 %}\3') + '\n'
        m_macro_end = macro_end.search(line)
        if m_macro_end:
            line = m_macro_end.expand(r'\1{% endmacro %}\2') + '\n'

        # Process line for single 'whole line' replacements
        m_macro_start = macro_start.search(line)
        m_macro_end = macro_end.search(line)
        m_if_start = if_start.search(line)
        m_if_else = if_else.search(line)
        m_if_elif = if_elif.search(line)
        m_if_end = if_end.search(line)
        m_for_start = for_start.search(line)
        m_for_end = for_end.search(line)
        m_namspace = namespace.search(line)
        m_inherit = inherit.search(line)
        m_block_single_line = block_single_line.search(line)
        m_block_start = block_start.search(line)
        m_block_end = block_end.search(line)

        m_comment_single_line = comment_single_line.search(line)

        if m_comment_single_line:
            output += m_comment_single_line.expand(r'{# \1 #}') + '\n'

        elif m_if_start:
            output += m_if_start.expand(r'\1{% if \2 %}\3') + '\n'
        elif m_if_else:
            output += m_if_else.expand(r'\1{% else %}\2') + '\n'
        elif m_if_elif:
            output += m_if_elif.expand(r'\1{% elif \2 %}\3') + '\n'
        elif m_if_end:
            output += m_if_end.expand(r'\1{% endif %}\2') + '\n'

        elif m_for_start:
            output += m_for_start.expand(r'\1{% for \2 %}\3') + '\n'
        elif m_for_end:
            output += m_for_end.expand(r'\1{% endfor %}\2') + '\n'

        elif m_namspace:
            output += m_namspace.expand(r"\1{% import '\3' as \2 with context %}\4") + '\n'
        elif m_inherit:
            output += m_inherit.expand(r"{% extends '\2' %}\3") + '\n'

        elif m_block_single_line:
            output += m_block_single_line.expand(r'\1{% block \2 %}\3{% endblock %}\4') + '\n'
        elif m_block_start:
            output += m_block_start.expand(r'\1{% block \2 %}\3') + '\n'
        elif m_block_end:
            output += m_block_end.expand(r'\1{% endblock %}\2') + '\n'

        else:
            # Doesn't match anything we're going to process, pass though
            output += line

    return output


def jinjify_shortcodes(in_dir, out_dir):
    for fname in os.listdir(in_dir):
        if not fname.endswith('.tmpl'):
            continue
        in_file = os.path.join(in_dir, fname)
        out_file = os.path.join(out_dir, fname)
        with open(in_file) as inf:
            data = mako2jinja(inf)
        with open(out_file, 'w') as outf:
            outf.write(data)


def usage():
    print("Usage: python {} [in-dir] [out-dir]".format(sys.argv[0]))
    print("OR")
    print("Usage: python {} [in-file] [out-file]".format(sys.argv[0]))

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print('Performing standard conversions:')
        for m, j in (
            ('nikola/data/themes/base', 'nikola/data/themes/base-jinja'),
            ('nikola/data/themes/bootstrap4', 'nikola/data/themes/bootstrap4-jinja')
        ):
            print('    {0} -> {1}'.format(m, j))
            jinjify(m, j)
        jinjify_shortcodes('nikola/data/shortcodes/mako', 'nikola/data/shortcodes/jinja')
    elif len(sys.argv) != 3:
        print('ERROR: needs input and output directory (file), or no arguments for default conversions.')
        usage()
    elif os.path.isdir(sys.argv[1]) and (os.path.isdir(sys.argv[2]) or not os.path.exists(sys.argv[2])):
        jinjify(sys.argv[1], sys.argv[2])
    elif os.path.isfile(sys.argv[1]) and (os.path.isfile(sys.argv[2]) or not os.path.exists(sys.argv[2])):
        tmpdir = tempfile.mkdtemp()
        indir = os.path.sep.join((tmpdir, 'in', 'templates'))
        outdir = os.path.sep.join((tmpdir, 'out', 'templates'))
        os.makedirs(indir)
        shutil.copy(sys.argv[1], indir)
        jinjify(os.path.dirname(indir), os.path.dirname(outdir))
        shutil.move(os.path.sep.join((outdir, os.path.basename(sys.argv[1]))), sys.argv[2])
    else:
        print('ERROR: the two arguments must be both directories or files')
        usage()
