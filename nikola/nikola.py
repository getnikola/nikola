# -*- coding: utf-8 -*-

import nikola
import os
import sys
from collections import defaultdict
import codecs
import glob
from gzip import GzipFile
import datetime
from copy import copy
import tempfile
import urlparse
import datetime
import re

from doit.reporter import ExecutedOnlyReporter
from doit.tools import InteractiveAction

# Use the less-verbose reporter
DOIT_CONFIG = {'reporter': ExecutedOnlyReporter}

########################################
# New post
########################################

# slugify is copied from
# http://code.activestate.com/recipes/577257-slugify-make-a-string-usable-in-a-url-or-filename/
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

    
def new_post(is_post = True):
    # Guess where we should put this
    for path, _, _, use_in_rss in post_pages:
        if use_in_rss == is_post:
            break
    
    print "Creating New Post"
    print "-----------------\n"
    title = raw_input("Enter title: ").decode(sys.stdin.encoding)
    slug = slugify(title)
    data = u'\n'.join([
        title,
        slug,
        datetime.datetime.now().strftime('%Y/%m/%d %H:%M')
        ])
    output_path = os.path.dirname(path)
    meta_path = os.path.join(output_path,slug+".meta")
    with codecs.open(meta_path, "wb+", "utf8") as fd:
        fd.write(data)
    txt_path = os.path.join(output_path,slug+".txt")
    with codecs.open(txt_path, "wb+", "utf8") as fd:
        fd.write(u"Write your post here.")
    print "Your post's metadata is at: ", meta_path
    print "Your post's text is at: ", txt_path

def new_page():
    new_post(False)
    

def task_new_post():
    """Create a new post (interactive)."""
    return {
        "uptodate": [True],
        "actions": [InteractiveAction("%s %s new_post" % (sys.executable, __file__))],
        }

def task_new_page():
    """Create a new post (interactive)."""
    return {
        "uptodate": [True],
        "actions": [InteractiveAction("%s %s new_page" % (sys.executable, __file__))],
        }


########################################
# Perform deployment
########################################

def task_deploy():
    """Deploy site. (Use -a option to execute)"""
    return {
        "uptodate": [True],
        "actions": DEPLOY_COMMANDS,
        "verbosity": 2,
        }

########################################
# Generate google sitemap
########################################

def task_sitemap():
    """Generate Google sitemap."""

    output_path = os.path.abspath("output")
    sitemap_path = os.path.join(output_path, "sitemap.xml.gz")
    
    def sitemap():
        # Generate config
        config_data = """<?xml version="1.0" encoding="UTF-8"?>
<site
  base_url="%s"
  store_into="%s"
  verbose="1" >
  <directory path="%s" url="%s" />
  <filter action="drop" type="wildcard" pattern="*~" />
  <filter action="drop" type="regexp" pattern="/\.[^/]*" />
</site>""" % (
            BLOG_URL,
            sitemap_path,
            output_path,
            BLOG_URL,
        )
        config_file = tempfile.NamedTemporaryFile(delete=False)
        config_file.write(config_data)
        config_file.close()

        # Generate sitemap
        import nikola.sitemap_gen as smap
        sitemap = smap.CreateSitemapFromFile(config_file.name, True)
        if not sitemap:
            smap.output.Log('Configuration file errors -- exiting.', 0)
        else:
            sitemap.Generate()
            smap.output.Log('Number of errors: %d' % smap.output.num_errors, 1)
            smap.output.Log('Number of warnings: %d' % smap.output.num_warns, 1)
        os.unlink(config_file.name)
            
    return {
        "task_dep": [
            "render_archive",
            "render_indexes",
            "render_pages",
            "render_posts",
            "render_rss",
            "render_sources",
            "render_tags"],
        "targets": [sitemap_path],
        "actions": [(sitemap,)],
        "clean": True,
        }


########################################
# Start local server on port 8000
########################################

def task_serve():
    """Start test server. (Usage: doit -a serve [-p 8000])"""
    
    def serve(port):
        from BaseHTTPServer import HTTPServer
        from SimpleHTTPServer import SimpleHTTPRequestHandler as handler

        os.chdir("output")
        
        httpd = HTTPServer (('127.0.0.1', port), handler)
        sa = httpd.socket.getsockname()
        print "Serving HTTP on", sa[0], "port", sa[1], "..."
        httpd.serve_forever()

    return {
        "uptodate": [True],
        "actions": [(serve,)],
        "verbosity": 2,
        "params": [{'short': 'p',
                 'name': 'port',
                 'long': 'port',
                 'type': int,
                 'default': 8000,
                 'help': 'Port number (default: 8000)'}],
        }


########################################
# Specialized post page tasks
########################################

def task_render_pages():
    """Build final pages from metadata and HTML fragments."""
    for lang in TRANSLATIONS:
        for wildcard, destination, template_name, _ in post_pages:
            template_name = os.path.join("templates", template_name)
            for task in generic_page_renderer(
                    lang, wildcard, template_name, destination):
                yield task

def task_render_sources():
    """Publish the rst sources because why not?"""
    for lang in TRANSLATIONS:
        for post in timeline:
            output_name = post.destination_path(lang, '.txt')
            source = post.source_path
            if lang != DEFAULT_LANG:
                source_lang = source + '.' + lang
                if os.path.exists(source_lang):
                    source = source_lang
            yield {
                'name': output_name.encode('utf8'),
                'file_dep': [source],
                'targets': [output_name],
                'actions': [(copy_file, (source, output_name))],
                'clean': True,
                }
                
########################################
# HTML Fragment rendererers
########################################


def task_render_posts():
    """Build HTML fragments from metadata and reSt."""
    for lang in TRANSLATIONS:
        for post in timeline:
            source = post.source_path
            dest = post.base_path           
            if lang != DEFAULT_LANG:
                dest += '.' + lang
                source_lang = source + '.' + lang
                if os.path.exists(source_lang):
                    source = source_lang
            yield {
                'name': dest.encode('utf-8'),
                'file_dep': post.fragment_deps(lang),
                'targets': [dest],
                'actions': [(nikola.compile_html, [source, dest])],
                'clean': True,                
            }

########################################
# Post archive renderers
########################################


def task_render_indexes():
    "Render 10-post-per-page indexes."
    template_name = os.path.join("templates", "index.tmpl")
    posts = [x for x in timeline if x.use_in_feeds]
    # Split in smaller lists
    lists = []
    while posts:
        lists.append(posts[:10])
        posts = posts[10:]
    for lang in TRANSLATIONS:
        for i, post_list in enumerate(lists):
            context = {}
            if not i:
                output_name = "index.html"
            else:
                output_name = "index-%s.html" % i
            context["prevlink"] = None
            if i > 1:
                context["prevlink"] = "index-%s.html" % (i - 1)
            if i == 1:
                context["prevlink"] = "index.html"
            context["nextlink"] = "index-%s.html" % (i + 1)
            output_name = os.path.join(
                'output', TRANSLATIONS[lang], INDEX_PATH, output_name)
            yield generic_post_list_renderer(
                lang,
                post_list,
                output_name,
                template_name,
                context,
            )


def task_render_archive():
    """Render the post archives."""
    # TODO add next/prev links for years
    template_name = os.path.join("templates", "list.tmpl")
    for year, posts in posts_per_year.items():
        for lang in TRANSLATIONS:
            output_name = os.path.join(
                "output", TRANSLATIONS[lang], INDEX_PATH, year, "index.html")
            post_list = [global_data[post] for post in posts]
            post_list.sort(cmp=lambda a, b: cmp(a.date, b.date))
            post_list.reverse()
            context = {}
            context["lang"] = lang
            context["items"] = [("[%s] %s" % (post.date, post.title(lang)), post.permalink(lang)) for post in post_list]
            context["title"] = "Posts for year %s" % year

            yield generic_post_list_renderer(
                lang,
                post_list,
                output_name,
                template_name,
                context,
            )

    # And global "all your years" page
    years = [int(x) for x in posts_per_year.keys()]
    years.sort(reverse=True)
    template_name = os.path.join("templates", "list.tmpl")
    for lang in TRANSLATIONS:
        output_name = os.path.join(
            "output", TRANSLATIONS[lang], INDEX_PATH, "archive.html")
        context["title"] = "Archive"
        context["title_es"] = u"Archivo"
        context["items"] = [(year, "%s/index.html" % year) for year in years]
        yield generic_post_list_renderer(
            lang,
            [],
            output_name,
            template_name,
            context,
        )


def task_render_tags():
    """Render the tag pages."""
    template_name = os.path.join("templates", "list.tmpl")
    for tag, posts in posts_per_tag.items():
        for lang in TRANSLATIONS:
            # Render HTML
            output_name = os.path.join(
                "output", TRANSLATIONS[lang], TAG_PATH, tag + ".html")
            post_list = [global_data[post] for post in posts]
            post_list.sort(cmp=lambda a, b: cmp(a.date, b.date))
            post_list.reverse()
            context = {}
            context["lang"] = lang
            context["title"] = "Posts about %s:" % tag
            context["items"] = [("[%s] %s" % (post.date, post.title(lang)), post.permalink(lang)) for post in post_list]
            
            yield generic_post_list_renderer(
                lang,
                post_list,
                output_name,
                template_name,
                context,
            )
            #Render RSS
            output_name = os.path.join(
                "output", TRANSLATIONS[lang], TAG_PATH, tag + ".xml")
            deps = []
            post_list = [global_data[post] for post in posts if global_data[post].use_in_feeds]
            post_list.sort(cmp=lambda a, b: cmp(a.date, b.date))
            post_list.reverse()
            for post in post_list:
                deps += post.deps(lang)
            yield {
                'name': output_name.encode('utf8'),
                'file_dep': deps,
                'targets': [output_name],
                'actions': [(generic_rss_renderer,
                    (lang, "%s (%s)" % (BLOG_TITLE, tag), BLOG_URL,
                    BLOG_DESCRIPTION, post_list, output_name))],
                'clean': True,
            }

    # And global "all your tags" page
    tags = posts_per_tag.keys()
    tags.sort()
    template_name = os.path.join("templates", "list.tmpl")
    for lang in TRANSLATIONS:
        output_name = os.path.join(
            "output", TRANSLATIONS[lang], TAG_PATH, "index.html")
        context = {}
        context["title"] = u"Tags"
        context["title_es"] = u"Tags"
        context["items"] = [(tag, "%s.html" % tag) for tag in tags]
        yield generic_post_list_renderer(
            lang,
            [],
            output_name,
            template_name,
            context,
        )


def task_render_rss():
    """Generate RSS feeds."""
    for lang in TRANSLATIONS:
        output_name = os.path.join("output", TRANSLATIONS[lang],
            RSS_PATH, "rss.xml")
        deps = []
        posts = [x for x in timeline if x.use_in_feeds][:10]
        for post in posts:
            deps += post.deps(lang)
        yield {
            'name': output_name,
            'file_dep': deps,
            'targets': [output_name],
            'actions': [(generic_rss_renderer,
                (lang, BLOG_TITLE, BLOG_URL,
                BLOG_DESCRIPTION, posts, output_name))],
            'clean': True,
        }    

def task_render_galleries():
    """Render image galleries."""
    template_name = os.path.join("templates", "gallery.tmpl")
    template = Template(
        filename=template_name,
        output_encoding='utf-8',
        module_directory='tmp',
        lookup=template_lookup)

    gallery_list = glob.glob("galleries/*")
    # Fail quick if we don't have galleries, so we don't
    # require PIL
    if not gallery_list:
        return
    import Image
    def create_thumb(src, dst):
        size = THUMBNAIL_SIZE, THUMBNAIL_SIZE
        im = Image.open(src)
        im.thumbnail(size, Image.ANTIALIAS)
        im.save(dst)
    
    # gallery_path is "gallery/name"
    for gallery_path in gallery_list:
        # gallery_name is "name"
        gallery_name = os.path.basename(gallery_path)
        # output_gallery is "output/GALLERY_PATH/name"
        output_gallery = os.path.join('output', GALLERY_PATH, gallery_name)
        # image_list contains "gallery/name/image_name.jpg"
        image_list = glob.glob(gallery_path+"/*jpg")
        image_list = [x for x in image_list if "thumbnail" not in x]
        image_name_list = [os.path.basename(x) for x in image_list]
        thumbs = []
        # Do thumbnails and copy originals
        for img, img_name in zip(image_list, image_name_list):
            # img is "galleries/name/image_name.jpg"
            # img_name is "image_name.jpg"
            # fname, ext are "image_name", ".jpg"
            fname, ext = os.path.splitext(img_name)
            # thumb_path is "output/GALLERY_PATH/name/image_name.thumbnail.jpg"
            thumb_path = os.path.join(output_gallery, fname +".thumbnail" + ext)
            # thumb_path is "output/GALLERY_PATH/name/image_name.jpg"
            orig_dest_path = os.path.join(output_gallery, img_name)
            thumbs.append(os.path.basename(thumb_path))
            yield {
                'name': thumb_path,
                'file_dep': [img],
                'targets': [thumb_path, orig_dest_path],
                'actions': [
                    (create_thumb, (img, thumb_path)),
                    (copy_file, (img, orig_dest_path))
                ],
                'clean': True,
            }
        output_name = os.path.join(output_gallery, "index.html")
        context = {}
        context ["lang"] = DEFAULT_LANG
        context ["title"] = os.path.basename(gallery_path)
        thumb_name_list = [os.path.basename(x) for x in thumbs]
        context["images"] = zip(image_name_list, thumb_name_list)

        # Use galleries/name/index.txt to generate a blurb for
        # the gallery, if it exists
        index_path = os.path.join(gallery_path, "index.txt")
        index_dst_path = os.path.join(gallery_path, "index.html")
        if os.path.exists(index_path):
            yield {
                'name': index_dst_path.encode('utf-8'),
                'file_dep': [index_path],
                'targets': [index_dst_path],
                'actions': [(nikola.compile_html, [index_path, index_dst_path])],
                'clean': True,
            }            
        
        def render_gallery(output_name, context, index_dst_path):
            if os.path.exists(index_dst_path):
                with codecs.open(index_dst_path, "rb", "utf8") as fd:
                    context['text'] = fd.read()
            else:
                context['text'] = ''
            render_template(template, output_name, context)

        yield {
            'name': gallery_path,
            'file_dep': [template_name] + image_list,
            'targets': [output_name],
            'actions': [(render_gallery, (output_name, context, index_dst_path))],
            'clean': True,
        }


def task_redirect():

    def create_redirect(src, dst):
        with codecs.open(src_path, "wb+", "utf8") as fd:
            fd.write('<head><meta HTTP-EQUIV="REFRESH" content="0; url=%s"></head>' % dst)
    
    for src, dst in REDIRECTIONS:
        src_path = os.path.join("output", src)
        yield {
            'name': src_path,
            'targets': [src_path],
            'actions': [(create_redirect, (src_path, dst))],
            'clean': True,
            }
        
########################################
# Utility functions (not tasks)
########################################

class Post(object):

    """Represents a blog post or web page."""

    def __init__(self, source_path, destination, use_in_feeds):
        """Initialize post.

        The base path is the .txt post file. From it we calculate
        the meta file, as well as any translations available, and
        the .html fragment file path.
        """
        self.use_in_feeds = use_in_feeds
        self.source_path = source_path # posts/blah.txt
        self.post_name = source_path.split(".", 1)[0]  # posts/blah
        self.base_path = self.post_name + ".html"  # posts/blah.html
        self.metadata_path =  self.post_name + ".meta"  # posts/blah.meta
        self.folder = destination
        with codecs.open(self.metadata_path, "r", "utf8") as meta_file:
            meta_data = meta_file.readlines()
        while len(meta_data) < 5:
            meta_data.append("")
        default_title, self.pagename, self.date, self.tags, self.link = \
            [x.strip() for x in meta_data]
        self.date = datetime.datetime.strptime(self.date, '%Y/%m/%d %H:%M')
        self.tags = [x.strip() for x in self.tags.split(',')]
        self.tags = filter(lambda x: x, self.tags)

        self.titles = {}
        # Load internationalized titles
        for lang in TRANSLATIONS:
            if lang == DEFAULT_LANG:
                self.titles[lang] = default_title
            else:
                metadata_path = self.metadata_path + "." + lang
                try:
                    with codecs.open(metadata_path, "r", "utf8") as meta_file:
                        self.titles[lang] = meta_file.readlines()[0].strip()
                except:
                    self.titles[lang] = default_title

    def title(self, lang):
        """Return localized title."""
        return self.titles[lang]

    def deps(self, lang):
        """Return a list of dependencies to build this post's page."""
        deps = [self.base_path]
        if lang != DEFAULT_LANG:
            deps += [ self.base_path + "." + lang]
        deps += self.fragment_deps(lang)
        return deps

    def fragment_deps(self, lang):
        """Return a list of dependencies to build this post's fragment."""
        deps = [self.source_path, self.metadata_path]
        if lang != DEFAULT_LANG:
            lang_deps = filter(os.path.exists, [ x + "." + lang for x in deps])
            deps += lang_deps
        return deps

    def text(self, lang):
        """Read the post file for that language and return its contents"""
        file_name = self.base_path
        if lang != DEFAULT_LANG:
            file_name_lang = file_name + ".%s" % lang
            if os.path.exists(file_name_lang):
                file_name = file_name_lang                
        with codecs.open(file_name, "r", "utf8") as post_file:
            data = post_file.read()
        return data

    def destination_path(self, lang, extension='.html'):
        path = os.path.join('output', TRANSLATIONS[lang],
            self.folder, self.pagename + extension)
        return path

    def permalink(self, lang=DEFAULT_LANG, absolute=False, extension='.html'):
        pieces = list(os.path.split(TRANSLATIONS[lang]))
        pieces += list(os.path.split(self.folder))
        pieces += [self.pagename + extension]
        pieces = filter(lambda x: x, pieces)
        if absolute:
            pieces = [BLOG_URL] + pieces
        else:
            pieces = [""] + pieces
        link = "/".join(pieces)
        return link


def set_temporal_structure():
    #"""Scan all metadata and create some data structures."""
    print "Parsing metadata"
    for wildcard, destination, _, use_in_feeds in post_pages:
        for base_path in glob.glob(wildcard):
            post = Post(base_path, destination, use_in_feeds)
            global_data[post.post_name] = post
            posts_per_year[str(post.date.year)].append(post.post_name)
            for tag in post.tags:
                posts_per_tag[tag].append(post.post_name)
    for name, post in global_data.items():
        timeline.append(post)
    timeline.sort(cmp=lambda a, b: cmp(a.date, b.date))
    timeline.reverse()

if __name__ != "__main__":
    global_data = {}
    posts_per_year = defaultdict(list)
    posts_per_tag = defaultdict(list)
    timeline = []
    set_temporal_structure()


########################################
# Mako template handlers
########################################

from mako.lookup import TemplateLookup
from mako.template import Template

template_lookup = TemplateLookup(
    directories=['.'],
    module_directory='tmp',
    )


post_tmpl = Template(
    filename=os.path.join("templates", "post.tmpl"),
    output_encoding='utf-8',
    module_directory='tmp',
    lookup=template_lookup)


def render_template(template, output_name, context):
    context.update(GLOBAL_CONTEXT)
    try:
        os.makedirs(os.path.dirname(output_name))
    except:
        pass
    with open(output_name, 'w+') as output:
        output.write(template.render(**context))


def generic_page_renderer(lang, wildcard, template_name, destination):
    """Render post fragments to final HTML pages."""
    for post in glob.glob(wildcard):
        post_name = post.split('.', 1)[0]
        template = Template(
            filename=template_name,
            output_encoding='utf-8',
            module_directory='tmp',
            lookup=template_lookup)
        meta_name = post_name + ".meta"
        context = {}
        post = global_data[post_name]        
        deps = post.deps(lang) + [template_name]
        context['post'] = post
        context['lang'] = lang
        context['title'] = post.title(lang)
        context['permalink'] = post.permalink(lang)
        output_name = os.path.join(
            "output", TRANSLATIONS[lang], destination,
            post.pagename + ".html")
        yield {
            'name': output_name.encode('utf-8'),
            'file_dep': deps, 
            'targets': [output_name],
            'actions': [(render_template, [template, output_name, context])],
            'clean': True,
        }


def generic_post_list_renderer(lang, posts, output_name, template_name,
    extra_context={}):
    """Renders pages with lists of posts."""

    deps = [template_name]
    for post in posts:
        deps += post.deps(lang)
    template = Template(
        filename=template_name,
        output_encoding='utf-8',
        module_directory='tmp',
        lookup=template_lookup)
    context = {}
    context["posts"] = posts
    context["title"] = BLOG_TITLE
    context["title_es"] = BLOG_TITLE
    context["permalink"] = "/posts/" + output_name
    context["permalink_es"] = "/es/posts/" + output_name
    context["lang"] = lang
    context["prevlink"] = None
    context["nextlink"] = None
    context.update(extra_context)
    return {
        'name': output_name.encode('utf8'),
        'targets': [output_name],
        'file_dep': deps,
        'actions': [(render_template, [template, output_name, context])],
        'clean': True,
    }


def generic_rss_renderer(lang, title, link, description, timeline, output_path):
    """Takes all necessary data, and renders a RSS feed in output_path."""
    items = []
    for post in timeline:
        args = {
            'title': post.title(lang),
            'link': post.permalink(lang),
            'description': post.text(lang),
            'guid': post.permalink(lang),
            'pubDate': post.date,
        }
        items.append(nikola.rss.RSSItem(**args))
    rss = nikola.rss.RSS2(
        title = title,
        link = link,
        description = description,
        lastBuildDate = datetime.datetime.now(),
        items = items,
        generator = 'nikola 1.0',
    )
    with open(output_path, "wb+") as rss_file:
        rss.write_xml(rss_file)

def copy_file(source, dest):
    with open(source, "rb") as input:
        with open(dest, "wb+") as output:
            output.write(input.read())

def nikola_main():
    if sys.argv[1] == "new_post":
        new_post()
    elif sys.argv[1] == "new_page":
        new_page()
    else:
        print "Starting doit..."
        os.system("doit -f %s" % __file__)
    