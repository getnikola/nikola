import codecs
import os
from urlparse import urlparse
from urllib import urlopen

from lxml import etree, html
from mako.template import Template

from nikola import utils

links = {}


def replacer(dst):
    return links.get(dst, dst)


def get_text_tag(tag, name, default):
    t = tag.find(name)
    if t is not None:
        return t.text
    else:
        return default


def import_attachment(item):
    post_type = get_text_tag(item,
        '{http://wordpress.org/export/1.2/}post_type', 'post')
    if post_type == 'attachment':
        url = get_text_tag(item,
            '{http://wordpress.org/export/1.2/}attachment_url', 'foo')
        link = get_text_tag(item,
            '{http://wordpress.org/export/1.2/}link', 'foo')
        path = urlparse(url).path
        dst_path = os.path.join(*(['new_site', 'files']
            + list(path.split('/'))))
        dst_dir = os.path.dirname(dst_path)
        if not os.path.isdir(dst_dir):
            os.makedirs(dst_dir)
        print "Downloading %s => %s" % (url, dst_path)
        with open(dst_path, 'wb+') as fd:
            fd.write(urlopen(url).read())
        dst_url = '/'.join(dst_path.split(os.sep)[2:])
        links[link] = '/' + dst_url
        links[url] = '/' + dst_url
    return


def import_item(item):
    """Takes an item from the feed and creates a post file."""
    title = get_text_tag(item, 'title', 'NO TITLE')
    # link is something like http://foo.com/2012/09/01/hello-world/
    # So, take the path, utils.slugify it, and that's our slug
    slug = utils.slugify(urlparse(get_text_tag(item, 'link', None)).path)
    description = get_text_tag(item, 'description', '')
    post_date = get_text_tag(item,
        '{http://wordpress.org/export/1.2/}post_date', None)
    post_type = get_text_tag(item,
        '{http://wordpress.org/export/1.2/}post_type', 'post')
    status = get_text_tag(item,
        '{http://wordpress.org/export/1.2/}status', 'publish')
    content = get_text_tag(item,
        '{http://purl.org/rss/1.0/modules/content/}encoded', '')

    tags = []
    if status != 'publish':
        tags.append('draft')
    for tag in item.findall('category'):
        text = tag.text
        if text == 'Uncategorized':
            continue
        tags.append(text)

    if post_type == 'attachment':
        return
    elif post_type == 'post':
        out_folder = 'posts'
    else:
        out_folder = 'stories'
    # Write metadata
    with codecs.open(os.path.join('new_site', out_folder, slug + '.meta'),
        "w+", "utf8") as fd:
        fd.write(u'%s\n' % title)
        fd.write(u'%s\n' % slug)
        fd.write(u'%s\n' % post_date)
        fd.write(u'%s\n' % ','.join(tags))
        fd.write(u'\n')
        fd.write(u'%s\n' % description)
    with open(os.path.join(
        'new_site', out_folder, slug + '.wp'), "wb+") as fd:
        if content.strip():
            try:
                doc = html.document_fromstring(content)
                doc.rewrite_links(replacer)
                fd.write(html.tostring(doc, encoding='utf8'))
            except:
                import pdb
                pdb.set_trace()


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
    context['BLOG_TITLE'] = get_text_tag(
        channel, 'title', 'PUT TITLE HERE')
    context['BLOG_DESCRIPTION'] = get_text_tag(
        channel, 'description', 'PUT DESCRIPTION HERE')
    context['BLOG_URL'] = get_text_tag(channel, 'link', '#')
    author = channel.find('{http://wordpress.org/export/1.2/}author')
    context['BLOG_EMAIL'] = get_text_tag(author,
        '{http://wordpress.org/export/1.2/}author_email', "joe@example.com")
    context['BLOG_AUTHOR'] = get_text_tag(author,
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
    conf_template = Template(filename=os.path.join(
        os.path.dirname(__file__), 'data', 'samplesite', 'conf.py.in'))
    with codecs.open(os.path.join('new_site', 'conf.py'), 'w+', 'utf8') as fd:
        fd.write(conf_template.render(**context))

    # Import posts
    for item in channel.findall('item'):
        import_attachment(item)
    for item in channel.findall('item'):
        import_item(item)
