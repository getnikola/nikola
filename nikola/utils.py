"""Utility functions."""

import PyRSS2Gen as rss

def get_compile_html(input_format='rest'):
    """Setup input format library."""
    if input_format == "rest":
        import rest
        compile_html = rest.compile_html
    elif input_format == "markdown":
        import md
        compile_html = md.compile_html
    return compile_html


def get_template_module(template_engine='mako'):
    """Setup templating library."""
    templates_module = None
    if template_engine == "mako":
        import mako_templates
        templates_module = mako_templates
    elif template_engine == "jinja":
        import jinja_templates
        templates_module = jinja_templates
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
        items.append(nikola.rss.RSSItem(**args))
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
