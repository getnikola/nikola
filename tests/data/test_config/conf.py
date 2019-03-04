# -*- coding: utf-8 -*-
import time

BLOG_AUTHOR = "Your Name"
BLOG_TITLE = "Demo Site"
SITE_URL = "https://example.com/"
BLOG_EMAIL = "joe@demo.site"
BLOG_DESCRIPTION = "This is a demo site for Nikola."
DEFAULT_LANG = "en"
CATEGORY_ALLOW_HIERARCHIES = False
CATEGORY_OUTPUT_FLAT_HIERARCHY = False
HIDDEN_CATEGORIES = []
HIDDEN_AUTHORS = ['Guest']
LICENSE = ""

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

ADDITIONAL_METADATA = {
    "ID": "conf"
}
