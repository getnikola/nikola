"""Utility functions."""

from collections import defaultdict
import datetime
import os
import re
import sys

import PyRSS2Gen as rss

__all__ = ['get_theme_path', 'get_theme_chain', 'load_messages', 'copy_tree',
    'get_compile_html', 'get_template_module', 'generic_rss_renderer',
    'copy_file', 'slugify']

def get_theme_path(theme):
    """Given a theme name, returns the path where its files are located.

    Looks in ./themes and in the place where themes go when installed.
    """
    dir_name = os.path.join('themes', theme)
    if os.path.isdir(dir_name):
        return dir_name
    dir_name = os.path.join(os.path.dirname(__file__),
        'data', 'themes', theme)
    if os.path.isdir(dir_name):
        return dir_name
    raise Exception(u"Can't find theme '%s'" % theme)


def get_theme_chain(theme):
    """Create the full theme inheritance chain."""
    themes = [theme]

    def get_parent(theme_name):
        parent_path = os.path.join('themes', theme_name, 'parent')
        parent_path = os.path.join(get_theme_path(theme_name), 'parent')
        if os.path.isfile(parent_path):
            with open(parent_path) as fd:
                return fd.readlines()[0].strip()
        return None

    while True:
        parent = get_parent(themes[-1])
        # Avoid silly loops
        if parent is None or parent in themes:
            break
        themes.append(parent)
    return themes


def load_messages(themes, translations):
    """ Load theme's messages into context.

    All the messages from parent themes are loaded,
    and "younger" themes have priority.
    """
    messages = defaultdict(dict)
    for theme_name in themes[::-1]:
        msg_folder = os.path.join(get_theme_path(theme_name), 'messages')
        oldpath = sys.path
        sys.path.insert(0, msg_folder)
        for lang in translations.keys():
            # If we don't do the reload, the module is cached
            translation = __import__(lang)
            reload(translation)
            messages[lang].update(translation.MESSAGES)
            del(translation)
        sys.path = oldpath
    return messages


def copy_tree(src, dst):
    """Copy a src tree to the dst folder.

    Example:

    src = "themes/default/assets"
    dst = "output/assets"

    should copy "themes/defauts/assets/foo/bar" to
    "output/assets/foo/bar"
    """
    ignore = set(['.svn'])
    base_len = len(src.split(os.sep))
    for root, dirs, files in os.walk(src):
        root_parts = root.split(os.sep)
        if set(root_parts) & ignore:
            continue
        dst_dir = os.path.join(dst, *root_parts[base_len:])
        if not os.path.isdir(dst_dir):
            os.makedirs(dst_dir)
        for src_name in files:
            dst_file = os.path.join(dst_dir, src_name)
            src_file = os.path.join(root, src_name)
            yield {
                'name': dst_file,
                'file_dep': [src_file],
                'targets': [dst_file],
                'actions': [(copy_file, (src_file, dst_file))],
                'clean': True,
            }


def get_compile_html(input_format):
    """Setup input format library."""
    if input_format == "rest":
        import rest
        compile_html = rest.compile_html
    elif input_format == "markdown":
        import md
        compile_html = md.compile_html
    return compile_html


def get_template_module(template_engine, themes):
    """Setup templating library."""
    templates_module = None
    if template_engine == "mako":
        import mako_templates
        templates_module = mako_templates
    elif template_engine == "jinja":
        import jinja_templates
        templates_module = jinja_templates
    templates_module.lookup = \
        templates_module.get_template_lookup(
        [os.path.join(get_theme_path(name), "templates")
            for name in themes])
    return templates_module


def generic_rss_renderer(lang, title, link, description,
    timeline, output_path):
    """Takes all necessary data, and renders a RSS feed in output_path."""
    items = []
    for post in timeline[:10]:
        args = {
            'title': post.title(lang),
            'link': post.permalink(lang),
            'description': post.text(lang),
            'guid': post.permalink(lang),
            'pubDate': post.date,
        }
        items.append(rss.RSSItem(**args))
    rss_obj = rss.RSS2(
        title=title,
        link=link,
        description=description,
        lastBuildDate=datetime.datetime.now(),
        items=items,
        generator='nikola 1.0',
    )
    dst_dir = os.path.dirname(output_path)
    if not os.path.isdir(dst_dir):
        os.makedirs(dst_dir)
    with open(output_path, "wb+") as rss_file:
        rss_obj.write_xml(rss_file)


def copy_file(source, dest):
    dst_dir = os.path.dirname(dest)
    if not os.path.isdir(dst_dir):
        os.makedirs(dst_dir)
    with open(source, "rb") as input:
        with open(dest, "wb+") as output:
            output.write(input.read())


# slugify is copied from
# http://code.activestate.com/recipes/
# 577257-slugify-make-a-string-usable-in-a-url-or-filename/
_slugify_strip_re = re.compile(r'[^\w\s-]')
_slugify_hyphenate_re = re.compile(r'[-\s]+')


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.

    From Django's "django/template/defaultfilters.py".
    """
    import unicodedata
    if not isinstance(value, unicode):
        value = unicode(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(_slugify_strip_re.sub('', value).strip().lower())
    return _slugify_hyphenate_re.sub('-', value)
