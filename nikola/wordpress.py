import codecs
import os
import sys
from urlparse import urlparse

from lxml import etree
from mako.template import Template

from nikola import utils

def get_text_tag(tag, name, default):
    t = tag.find(name)
    if t is not None:
        return t.text
    else:
        return default

def import_item(item):
    """Takes an item from the feed and creates a post file."""
    title = get_text_tag(item, 'title', 'NO TITLE')
    # link is something like http://foo.com/2012/09/01/hello-world/
    # So, take the path, utils.slugify it, and that's our slug
    slug = utils.slugify(urlparse(get_text_tag(item, 'link', None)).path)
    description = get_text_tag(item, 'description', '')
    post_date = get_text_tag(item, '{http://wordpress.org/export/1.2/}post_date', None)
    post_type = get_text_tag(item, '{http://wordpress.org/export/1.2/}post_type', 'post')
    status = get_text_tag(item, '{http://wordpress.org/export/1.2/}status', 'publish')
    content = get_text_tag(item, '{http://purl.org/rss/1.0/modules/content/}encoded', '')

    tags = []
    if status != 'publish':
        tags.append('draft')
    for tag in item.findall('category'):
        text = tag.text
        if text == 'Uncategorized':
            continue
        tags.append(text)

    if post_type == 'post':
        out_folder = 'posts'
    else:
        out_folder = 'stories'
    # Write metadata
    with codecs.open(os.path.join('new_site', out_folder, slug+'.meta'), "w+", "utf8") as fd:
        fd.write(u'%s\n' % title)
        fd.write(u'%s\n' % slug)
        fd.write(u'%s\n' % post_date)
        fd.write(u'%s\n' % ','.join(tags))
        fd.write(u'\n')
        fd.write(u'%s\n' % description)
    with codecs.open(os.path.join('new_site', out_folder, slug+'.wp'), "w+", "utf8") as fd:
        fd.write(content)


def process(fname):
    # Parse the data
    context = {}
    with open(fname) as fd:
        xml = []
        for line in fd:
            # These explode etree and are useless
            if '<atom:link rel=' in line:
                continue
            xml.append(line)
        xml = '\n'.join(xml)

    tree = etree.fromstring(xml)
    channel = tree.find('channel')

    context['DEFAULT_LANG'] = get_text_tag(channel, 'language', 'en')
    context['BLOG_TITLE'] = get_text_tag(channel, 'title', 'PUT TITLE HERE')
    context['BLOG_DESCRIPTION'] =  get_text_tag(channel, 'description', 'PUT DESCRIPTION HERE')
    context['BLOG_URL'] =  get_text_tag(channel, 'link', '#')
    author = channel.find('{http://wordpress.org/export/1.2/}author')
    context['BLOG_EMAIL'] =  get_text_tag(author,
        '{http://wordpress.org/export/1.2/}author_email', "joe@example.com")
    context['BLOG_AUTHOR'] =  get_text_tag(author,
        '{http://wordpress.org/export/1.2/}author_display_name', "Joe Example")
    context['POST_PAGES'] = '''(
        ("posts/*.wp", "posts", "post.tmpl", True),
        ("stories/*.wp", "stories", "story.tmpl", False),
    )'''
    context['POST_COMPILERS'] = '''{
    "rest": ('.txt', '.rst'),
    "markdown": ('.md', '.mdown', '.markdown', '.wp'),
    "html": ('.html', '.htm')
    }
    '''

    # Generate base site
    os.system('nikola init new_site')
    conf_template = Template(filename = os.path.join(
        os.path.dirname(__file__), 'data', 'samplesite', 'conf.py.in'))
    with codecs.open(os.path.join('new_site', 'conf.py'), 'w+', 'utf8') as fd:
        fd.write(conf_template.render(**context))

    # Import posts
    for item in channel.findall('item'):
        import_item(item)
