# -*- coding: utf-8 -*-

import nikola
import os
from collections import defaultdict
import codecs
import glob
import datetime
from copy import copy
import urlparse

########################################
# Specialized post page tasks
########################################

def task_render_page():
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
                'actions': [(copy_file, (source, output_name))]
                }
                
########################################
# HTML Fragment rendererers
########################################


def task_render_post():
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
                    BLOG_DESCRIPTION, post_list, output_name))]
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
                BLOG_DESCRIPTION, posts, output_name))]
        }    

        
########################################
# Utility functions (not tasks)
########################################


def permalink_year(year):
    return("http://lateral.netmanagers.com.ar/weblog/%s/index.html" % year)


def permalink_year_es(year):
    return("http://lateral.netmanagers.com.ar/tr/es/weblog/%s/index.html"
        % year)


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
        with open(dest, "wb=") as output:
            output.write(input.read())
