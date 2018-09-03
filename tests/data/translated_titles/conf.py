# -*- coding: utf-8 -*-
import time
BLOG_AUTHOR = "Your Name"  # (translatable)
BLOG_TITLE = "Demo Site"  # (translatable)
SITE_URL = "https://example.com/"
BLOG_EMAIL = "joe@demo.site"
BLOG_DESCRIPTION = "This is a demo site for Nikola."  # (translatable)
DEFAULT_LANG = "en"
TRANSLATIONS = {
    "en": "",
    "pl": "./pl",
}
TRANSLATIONS_PATTERN = "{path}.{lang}.{ext}"
NAVIGATION_LINKS = {
    DEFAULT_LANG: (
        ('/archive.html', 'Archives'),
        ('/categories/index.html', 'Tags'),
        ('/rss.xml', 'RSS'),
    ),
}
POSTS = (
    ("posts/*.rst", "posts", "post.tmpl"),
    ("posts/*.txt", "posts", "post.tmpl"),
)
PAGES = (
    ("pages/*.rst", "pages", "page.tmpl"),
    ("pages/*.txt", "pages", "page.tmpl"),
)
COMPILERS = {
    "rest": ('.rst', '.txt'),
    "markdown": ('.md', '.mdown', '.markdown'),
    "textile": ('.textile',),
    "txt2tags": ('.t2t',),
    "bbcode": ('.bb',),
    "wiki": ('.wiki',),
    "ipynb": ('.ipynb',),
    "html": ('.html', '.htm'),
    # PHP files are rendered the usual way (i.e. with the full templates).
    # The resulting files have .php extensions, making it possible to run
    # them without reconfiguring your server to recognize them.
    "php": ('.php',),
    # Pandoc detects the input from the source filename
    # but is disabled by default as it would conflict
    # with many of the others.
    # "pandoc": ('.rst', '.md', '.txt'),
}
REDIRECTIONS = []
THEME = "bootblog4"
LICENSE = ""
CONTENT_FOOTER = 'Contents &copy; {date}         <a href="mailto:{email}">{author}</a> - Powered by         <a href="https://getnikola.com/" rel="nofollow">Nikola</a>         {license}'
CONTENT_FOOTER_FORMATS = {
    DEFAULT_LANG: (
        (),
        {
            "email": BLOG_EMAIL,
            "author": BLOG_AUTHOR,
            "date": time.gmtime().tm_year,
            "license": LICENSE
        }
    )
}
COMMENT_SYSTEM = "disqus"
COMMENT_SYSTEM_ID = "nikolademo"
GLOBAL_CONTEXT = {}
