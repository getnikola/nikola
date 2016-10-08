# -*- coding: utf-8 -*-

# Copyright © 2012-2016 Roberto Alsina and others.

# Permission is hereby granted, free of charge, to any
# person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the
# Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the
# Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice
# shall be included in all copies or substantial portions of
# the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
# OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""Import a WordPress dump."""

from __future__ import unicode_literals, print_function
import os
import re
import sys
import datetime
import io
import json
import requests
from lxml import etree
from collections import defaultdict

try:
    import html2text
except:
    html2text = None

try:
    from urlparse import urlparse
    from urllib import unquote
except ImportError:
    from urllib.parse import urlparse, unquote  # NOQA

try:
    import phpserialize
except ImportError:
    phpserialize = None  # NOQA

from nikola.plugin_categories import Command
from nikola import utils
from nikola.utils import req_missing, unicode_str
from nikola.plugins.basic_import import ImportMixin, links
from nikola.nikola import DEFAULT_TRANSLATIONS_PATTERN
from nikola.plugins.command.init import SAMPLE_CONF, prepare_config, format_default_translations_config

LOGGER = utils.get_logger('import_wordpress', utils.STDERR_HANDLER)


def install_plugin(site, plugin_name, output_dir=None, show_install_notes=False):
    """Install a Nikola plugin."""
    LOGGER.notice("Installing plugin '{0}'".format(plugin_name))
    # Get hold of the 'plugin' plugin
    plugin_installer_info = site.plugin_manager.getPluginByName('plugin', 'Command')
    if plugin_installer_info is None:
        LOGGER.error('Internal error: cannot find the "plugin" plugin which is supposed to come with Nikola!')
        return False
    if not plugin_installer_info.is_activated:
        # Someone might have disabled the plugin in the `conf.py` used
        site.plugin_manager.activatePluginByName(plugin_installer_info.name)
        plugin_installer_info.plugin_object.set_site(site)
    plugin_installer = plugin_installer_info.plugin_object
    # Try to install the requested plugin
    options = {}
    for option in plugin_installer.cmd_options:
        options[option['name']] = option['default']
    options['install'] = plugin_name
    options['output_dir'] = output_dir
    options['show_install_notes'] = show_install_notes
    if plugin_installer.execute(options=options) > 0:
        return False
    # Let the plugin manager find newly installed plugins
    site.plugin_manager.collectPlugins()
    # Re-scan for compiler extensions
    site.compiler_extensions = site._activate_plugins_of_category("CompilerExtension")
    return True


class CommandImportWordpress(Command, ImportMixin):
    """Import a WordPress dump."""

    name = "import_wordpress"
    needs_config = False
    doc_usage = "[options] wordpress_export_file"
    doc_purpose = "import a WordPress dump"
    cmd_options = ImportMixin.cmd_options + [
        {
            'name': 'exclude_drafts',
            'long': 'no-drafts',
            'short': 'd',
            'default': False,
            'type': bool,
            'help': "Don't import drafts",
        },
        {
            'name': 'exclude_privates',
            'long': 'exclude-privates',
            'default': False,
            'type': bool,
            'help': "Don't import private posts",
        },
        {
            'name': 'include_empty_items',
            'long': 'include-empty-items',
            'default': False,
            'type': bool,
            'help': "Include empty posts and pages",
        },
        {
            'name': 'squash_newlines',
            'long': 'squash-newlines',
            'default': False,
            'type': bool,
            'help': "Shorten multiple newlines in a row to only two newlines",
        },
        {
            'name': 'no_downloads',
            'long': 'no-downloads',
            'default': False,
            'type': bool,
            'help': "Do not try to download files for the import",
        },
        {
            'name': 'download_auth',
            'long': 'download-auth',
            'default': None,
            'type': str,
            'help': "Specify username and password for HTTP authentication (separated by ':')",
        },
        {
            'name': 'separate_qtranslate_content',
            'long': 'qtranslate',
            'default': False,
            'type': bool,
            'help': "Look for translations generated by qtranslate plugin",
            # WARNING: won't recover translated titles that actually
            # don't seem to be part of the wordpress XML export at the
            # time of writing :(
        },
        {
            'name': 'translations_pattern',
            'long': 'translations_pattern',
            'default': None,
            'type': str,
            'help': "The pattern for translation files names",
        },
        {
            'name': 'export_categories_as_categories',
            'long': 'export-categories-as-categories',
            'default': False,
            'type': bool,
            'help': "Export categories as categories, instead of treating them as tags",
        },
        {
            'name': 'export_comments',
            'long': 'export-comments',
            'default': False,
            'type': bool,
            'help': "Export comments as .wpcomment files",
        },
        {
            'name': 'html2text',
            'long': 'html2text',
            'default': False,
            'type': bool,
            'help': "Uses html2text (needs to be installed with pip) to transform WordPress posts to MarkDown during import",
        },
        {
            'name': 'transform_to_markdown',
            'long': 'transform-to-markdown',
            'default': False,
            'type': bool,
            'help': "Uses WordPress page compiler to transform WordPress posts to HTML and then use html2text to transform them to MarkDown during import",
        },
        {
            'name': 'transform_to_html',
            'long': 'transform-to-html',
            'default': False,
            'type': bool,
            'help': "Uses WordPress page compiler to transform WordPress posts directly to HTML during import",
        },
        {
            'name': 'use_wordpress_compiler',
            'long': 'use-wordpress-compiler',
            'default': False,
            'type': bool,
            'help': "Instead of converting posts to markdown, leave them as is and use the WordPress page compiler",
        },
        {
            'name': 'install_wordpress_compiler',
            'long': 'install-wordpress-compiler',
            'default': False,
            'type': bool,
            'help': "Automatically installs the WordPress page compiler (either locally or in the new site) if required by other options.\nWarning: the compiler is GPL software!",
        },
        {
            'name': 'tag_sanitizing_strategy',
            'long': 'tag-sanitizing-strategy',
            'default': 'first',
            'help': 'lower: Convert all tag and category names to lower case\nfirst: Keep first spelling of tag or category name',
        },
        {
            'name': 'one_file',
            'long': 'one-file',
            'default': False,
            'type': bool,
            'help': "Save imported posts in the more modern one-file format.",
        },
    ]
    all_tags = set([])

    def _get_compiler(self):
        """Return whatever compiler we will use."""
        self._find_wordpress_compiler()
        if self.wordpress_page_compiler is not None:
            return self.wordpress_page_compiler
        plugin_info = self.site.plugin_manager.getPluginByName('markdown', 'PageCompiler')
        if plugin_info is not None:
            if not plugin_info.is_activated:
                self.site.plugin_manager.activatePluginByName(plugin_info.name)
                plugin_info.plugin_object.set_site(self.site)
            return plugin_info.plugin_object
        else:
            LOGGER.error("Can't find markdown post compiler.")

    def _find_wordpress_compiler(self):
        """Find WordPress compiler plugin."""
        if self.wordpress_page_compiler is not None:
            return
        plugin_info = self.site.plugin_manager.getPluginByName('wordpress', 'PageCompiler')
        if plugin_info is not None:
            if not plugin_info.is_activated:
                self.site.plugin_manager.activatePluginByName(plugin_info.name)
                plugin_info.plugin_object.set_site(self.site)
            self.wordpress_page_compiler = plugin_info.plugin_object

    def _read_options(self, options, args):
        """Read command-line options."""
        options['filename'] = args.pop(0)

        if args and ('output_folder' not in args or
                     options['output_folder'] == 'new_site'):
            options['output_folder'] = args.pop(0)

        if args:
            LOGGER.warn('You specified additional arguments ({0}). Please consider '
                        'putting these arguments before the filename if you '
                        'are running into problems.'.format(args))

        self.onefile = options.get('one_file', False)

        self.import_into_existing_site = False
        self.url_map = {}
        self.timezone = None

        self.wordpress_export_file = options['filename']
        self.squash_newlines = options.get('squash_newlines', False)
        self.output_folder = options.get('output_folder', 'new_site')

        self.exclude_drafts = options.get('exclude_drafts', False)
        self.exclude_privates = options.get('exclude_privates', False)
        self.no_downloads = options.get('no_downloads', False)
        self.import_empty_items = options.get('include_empty_items', False)

        self.export_categories_as_categories = options.get('export_categories_as_categories', False)
        self.export_comments = options.get('export_comments', False)

        self.html2text = options.get('html2text', False)
        self.transform_to_markdown = options.get('transform_to_markdown', False)

        self.transform_to_html = options.get('transform_to_html', False)
        self.use_wordpress_compiler = options.get('use_wordpress_compiler', False)
        self.install_wordpress_compiler = options.get('install_wordpress_compiler', False)
        self.wordpress_page_compiler = None

        self.tag_saniziting_strategy = options.get('tag_saniziting_strategy', 'first')

        self.auth = None
        if options.get('download_auth') is not None:
            username_password = options.get('download_auth')
            self.auth = tuple(username_password.split(':', 1))
            if len(self.auth) < 2:
                LOGGER.error("Please specify HTTP authentication credentials in the form username:password.")
                return False

        self.separate_qtranslate_content = options.get('separate_qtranslate_content')
        self.translations_pattern = options.get('translations_pattern')

        count = (1 if self.html2text else 0) + (1 if self.transform_to_html else 0) + (1 if self.transform_to_markdown else 0)
        if count > 1:
            LOGGER.error("You can use at most one of the options --html2text, --transform-to-html and --transform-to-markdown.")
            return False
        if (self.html2text or self.transform_to_html or self.transform_to_markdown) and self.use_wordpress_compiler:
            LOGGER.warn("It does not make sense to combine --use-wordpress-compiler with any of --html2text, --transform-to-html and --transform-to-markdown, as the latter convert all posts to HTML and the first option then affects zero posts.")

        if (self.html2text or self.transform_to_markdown) and not html2text:
            LOGGER.error("You need to install html2text via 'pip install html2text' before you can use the --html2text and --transform-to-markdown options.")
            return False

        if self.transform_to_html or self.transform_to_markdown:
            self._find_wordpress_compiler()
            if not self.wordpress_page_compiler and self.install_wordpress_compiler:
                if not install_plugin(self.site, 'wordpress_compiler', output_dir='plugins'):  # local install
                    return False
                self._find_wordpress_compiler()
            if not self.wordpress_page_compiler:
                LOGGER.error("To compile WordPress posts to HTML, the WordPress post compiler is needed. You can install it via:")
                LOGGER.error("    nikola plugin -i wordpress_compiler")
                LOGGER.error("Please note that the WordPress post compiler is licensed under the GPL v2.")
                return False

        return True

    def _prepare(self, channel):
        """Prepare context and category hierarchy."""
        self.context = self.populate_context(channel)
        self.base_dir = urlparse(self.context['BASE_URL']).path

        if self.export_categories_as_categories:
            wordpress_namespace = channel.nsmap['wp']
            cat_map = dict()
            for cat in channel.findall('{{{0}}}category'.format(wordpress_namespace)):
                # cat_id = get_text_tag(cat, '{{{0}}}term_id'.format(wordpress_namespace), None)
                cat_slug = get_text_tag(cat, '{{{0}}}category_nicename'.format(wordpress_namespace), None)
                cat_parent_slug = get_text_tag(cat, '{{{0}}}category_parent'.format(wordpress_namespace), None)
                cat_name = get_text_tag(cat, '{{{0}}}cat_name'.format(wordpress_namespace), None)
                cat_path = [cat_name]
                if cat_parent_slug in cat_map:
                    cat_path = cat_map[cat_parent_slug] + cat_path
                cat_map[cat_slug] = cat_path
            self._category_paths = dict()
            for cat, path in cat_map.items():
                self._category_paths[cat] = utils.join_hierarchical_category_path(path)

    def _execute(self, options={}, args=[]):
        """Import a WordPress blog from an export file into a Nikola site."""
        if not args:
            print(self.help())
            return False

        if not self._read_options(options, args):
            return False

        # A place holder where extra language (if detected) will be stored
        self.extra_languages = set()

        if not self.no_downloads:
            def show_info_about_mising_module(modulename):
                LOGGER.error(
                    'To use the "{commandname}" command, you have to install '
                    'the "{package}" package or supply the "--no-downloads" '
                    'option.'.format(
                        commandname=self.name,
                        package=modulename)
                )

            if phpserialize is None:
                req_missing(['phpserialize'], 'import WordPress dumps without --no-downloads')

        channel = self.get_channel_from_file(self.wordpress_export_file)
        self._prepare(channel)
        conf_template = self.generate_base_site()

        # If user  has specified a custom pattern for translation files we
        # need to fix the config
        if self.translations_pattern:
            self.context['TRANSLATIONS_PATTERN'] = self.translations_pattern

        self.import_posts(channel)

        self.context['TRANSLATIONS'] = format_default_translations_config(
            self.extra_languages)
        self.context['REDIRECTIONS'] = self.configure_redirections(
            self.url_map, self.base_dir)
        if self.timezone:
            self.context['TIMEZONE'] = self.timezone
        if self.export_categories_as_categories:
            self.context['CATEGORY_ALLOW_HIERARCHIES'] = True
            self.context['CATEGORY_OUTPUT_FLAT_HIERARCHY'] = True

        # Add tag redirects
        for tag in self.all_tags:
            try:
                if isinstance(tag, utils.bytes_str):
                    tag_str = tag.decode('utf8', 'replace')
                else:
                    tag_str = tag
            except AttributeError:
                tag_str = tag
            tag = utils.slugify(tag_str, self.lang)
            src_url = '{}tag/{}'.format(self.context['SITE_URL'], tag)
            dst_url = self.site.link('tag', tag)
            if src_url != dst_url:
                self.url_map[src_url] = dst_url

        self.write_urlmap_csv(
            os.path.join(self.output_folder, 'url_map.csv'), self.url_map)
        rendered_template = conf_template.render(**prepare_config(self.context))
        self.write_configuration(self.get_configuration_output_path(),
                                 rendered_template)

        if self.use_wordpress_compiler:
            if self.install_wordpress_compiler:
                if not install_plugin(self.site, 'wordpress_compiler', output_dir=os.path.join(self.output_folder, 'plugins')):
                    return False
            else:
                LOGGER.warn("Make sure to install the WordPress page compiler via")
                LOGGER.warn("    nikola plugin -i wordpress_compiler")
                LOGGER.warn("in your imported blog's folder ({0}), if you haven't installed it system-wide or user-wide. Otherwise, your newly imported blog won't compile.".format(self.output_folder))

    @classmethod
    def read_xml_file(cls, filename):
        """Read XML file into memory."""
        xml = []

        with open(filename, 'rb') as fd:
            for line in fd:
                # These explode etree and are useless
                if b'<atom:link rel=' in line:
                    continue
                xml.append(line)
        return b''.join(xml)

    @classmethod
    def get_channel_from_file(cls, filename):
        """Get channel from XML file."""
        tree = etree.fromstring(cls.read_xml_file(filename))
        channel = tree.find('channel')
        return channel

    def populate_context(self, channel):
        """Populate context with config for the site."""
        wordpress_namespace = channel.nsmap['wp']

        context = SAMPLE_CONF.copy()
        self.lang = get_text_tag(channel, 'language', 'en')[:2]
        context['DEFAULT_LANG'] = self.lang
        context['TRANSLATIONS_PATTERN'] = DEFAULT_TRANSLATIONS_PATTERN
        context['BLOG_TITLE'] = get_text_tag(channel, 'title',
                                             'PUT TITLE HERE')
        context['BLOG_DESCRIPTION'] = get_text_tag(
            channel, 'description', 'PUT DESCRIPTION HERE')
        context['BASE_URL'] = get_text_tag(channel, 'link', '#')
        if not context['BASE_URL']:
            base_site_url = channel.find('{{{0}}}author'.format(wordpress_namespace))
            context['BASE_URL'] = get_text_tag(base_site_url,
                                               None,
                                               "http://foo.com/")
        if not context['BASE_URL'].endswith('/'):
            context['BASE_URL'] += '/'
        context['SITE_URL'] = context['BASE_URL']

        author = channel.find('{{{0}}}author'.format(wordpress_namespace))
        context['BLOG_EMAIL'] = get_text_tag(
            author,
            '{{{0}}}author_email'.format(wordpress_namespace),
            "joe@example.com")
        context['BLOG_AUTHOR'] = get_text_tag(
            author,
            '{{{0}}}author_display_name'.format(wordpress_namespace),
            "Joe Example")
        extensions = ['rst', 'txt', 'md', 'html']
        if self.use_wordpress_compiler:
            extensions.append('wp')
        POSTS = '(\n'
        PAGES = '(\n'
        for extension in extensions:
            POSTS += '    ("posts/*.{0}", "posts", "post.tmpl"),\n'.format(extension)
            PAGES += '    ("pages/*.{0}", "pages", "story.tmpl"),\n'.format(extension)
        POSTS += ')\n'
        PAGES += ')\n'
        context['POSTS'] = POSTS
        context['PAGES'] = PAGES
        COMPILERS = '{\n'
        COMPILERS += '''    "rest": ('.txt', '.rst'),''' + '\n'
        COMPILERS += '''    "markdown": ('.md', '.mdown', '.markdown'),''' + '\n'
        COMPILERS += '''    "html": ('.html', '.htm'),''' + '\n'
        if self.use_wordpress_compiler:
            COMPILERS += '''    "wordpress": ('.wp'),''' + '\n'
        COMPILERS += '}'
        context['COMPILERS'] = COMPILERS

        return context

    def download_url_content_to_file(self, url, dst_path):
        """Download some content (attachments) to a file."""
        try:
            request = requests.get(url, auth=self.auth)
            if request.status_code >= 400:
                LOGGER.warn("Downloading {0} to {1} failed with HTTP status code {2}".format(url, dst_path, request.status_code))
                return
            with open(dst_path, 'wb+') as fd:
                fd.write(request.content)
        except requests.exceptions.ConnectionError as err:
            LOGGER.warn("Downloading {0} to {1} failed: {2}".format(url, dst_path, err))

    def import_attachment(self, item, wordpress_namespace):
        """Import an attachment to the site."""
        # Download main image
        url = get_text_tag(
            item, '{{{0}}}attachment_url'.format(wordpress_namespace), 'foo')
        link = get_text_tag(item, '{{{0}}}link'.format(wordpress_namespace),
                            'foo')
        path = urlparse(url).path
        dst_path = os.path.join(*([self.output_folder, 'files'] + list(path.split('/'))))
        if self.no_downloads:
            LOGGER.info("Skipping downloading {0} => {1}".format(url, dst_path))
        else:
            dst_dir = os.path.dirname(dst_path)
            utils.makedirs(dst_dir)
            LOGGER.info("Downloading {0} => {1}".format(url, dst_path))
            self.download_url_content_to_file(url, dst_path)
        dst_url = '/'.join(dst_path.split(os.sep)[2:])
        links[link] = '/' + dst_url
        links[url] = '/' + dst_url

        files = [path]
        files_meta = [{}]

        additional_metadata = item.findall('{{{0}}}postmeta'.format(wordpress_namespace))
        if phpserialize and additional_metadata:
            source_path = os.path.dirname(url)
            for element in additional_metadata:
                meta_key = element.find('{{{0}}}meta_key'.format(wordpress_namespace))
                if meta_key is not None and meta_key.text == '_wp_attachment_metadata':
                    meta_value = element.find('{{{0}}}meta_value'.format(wordpress_namespace))

                    if meta_value is None:
                        continue

                    # Someone from Wordpress thought it was a good idea
                    # serialize PHP objects into that metadata field. Given
                    # that the export should give you the power to insert
                    # your blogging into another site or system its not.
                    # Why don't they just use JSON?
                    if sys.version_info[0] == 2:
                        try:
                            metadata = phpserialize.loads(utils.sys_encode(meta_value.text))
                        except ValueError:
                            # local encoding might be wrong sometimes
                            metadata = phpserialize.loads(meta_value.text.encode('utf-8'))
                    else:
                        metadata = phpserialize.loads(meta_value.text.encode('utf-8'))

                    meta_key = b'image_meta'
                    size_key = b'sizes'
                    file_key = b'file'
                    width_key = b'width'
                    height_key = b'height'

                    # Extract metadata
                    if width_key in metadata and height_key in metadata:
                        files_meta[0]['width'] = int(metadata[width_key])
                        files_meta[0]['height'] = int(metadata[height_key])

                    if meta_key in metadata:
                        image_meta = metadata[meta_key]
                        if not image_meta:
                            continue
                        dst_meta = {}

                        def add(our_key, wp_key, is_int=False, ignore_zero=False, is_float=False):
                            if wp_key in image_meta:
                                value = image_meta[wp_key]
                                if is_int:
                                    value = int(value)
                                    if ignore_zero and value == 0:
                                        return
                                elif is_float:
                                    value = float(value)
                                    if ignore_zero and value == 0:
                                        return
                                else:
                                    value = value.decode('utf-8')  # assume UTF-8
                                    if value == '':  # skip empty values
                                        return
                                dst_meta[our_key] = value

                        add('aperture', b'aperture', is_float=True, ignore_zero=True)
                        add('credit', b'credit')
                        add('camera', b'camera')
                        add('caption', b'caption')
                        add('created_timestamp', b'created_timestamp', is_float=True, ignore_zero=True)
                        add('copyright', b'copyright')
                        add('focal_length', b'focal_length', is_float=True, ignore_zero=True)
                        add('iso', b'iso', is_float=True, ignore_zero=True)
                        add('shutter_speed', b'shutter_speed', ignore_zero=True, is_float=True)
                        add('title', b'title')

                        if len(dst_meta) > 0:
                            files_meta[0]['meta'] = dst_meta

                    # Find other sizes of image
                    if size_key not in metadata:
                        continue

                    for size in metadata[size_key]:
                        filename = metadata[size_key][size][file_key]
                        url = '/'.join([source_path, filename.decode('utf-8')])

                        # Construct metadata
                        meta = {}
                        meta['size'] = size.decode('utf-8')
                        if width_key in metadata[size_key][size] and height_key in metadata[size_key][size]:
                            meta['width'] = int(metadata[size_key][size][width_key])
                            meta['height'] = int(metadata[size_key][size][height_key])

                        path = urlparse(url).path
                        dst_path = os.path.join(*([self.output_folder, 'files'] + list(path.split('/'))))
                        if self.no_downloads:
                            LOGGER.info("Skipping downloading {0} => {1}".format(url, dst_path))
                        else:
                            dst_dir = os.path.dirname(dst_path)
                            utils.makedirs(dst_dir)
                            LOGGER.info("Downloading {0} => {1}".format(url, dst_path))
                            self.download_url_content_to_file(url, dst_path)
                        dst_url = '/'.join(dst_path.split(os.sep)[2:])
                        links[url] = '/' + dst_url

                        files.append(path)
                        files_meta.append(meta)

        # Prepare result
        result = {}
        result['files'] = files
        result['files_meta'] = files_meta

        # Prepare extraction of more information
        dc_namespace = item.nsmap['dc']
        content_namespace = item.nsmap['content']
        excerpt_namespace = item.nsmap['excerpt']

        def add(result_key, key, namespace=None, filter=None, store_empty=False):
            if namespace is not None:
                value = get_text_tag(item, '{{{0}}}{1}'.format(namespace, key), None)
            else:
                value = get_text_tag(item, key, None)
            if value is not None:
                if filter:
                    value = filter(value)
                if value or store_empty:
                    result[result_key] = value

        add('title', 'title')
        add('date_utc', 'post_date_gmt', namespace=wordpress_namespace)
        add('wordpress_user_name', 'creator', namespace=dc_namespace)
        add('content', 'encoded', namespace=content_namespace)
        add('excerpt', 'encoded', namespace=excerpt_namespace)
        add('description', 'description')

        return result

    code_re1 = re.compile(r'\[code.* lang.*?="(.*?)?".*\](.*?)\[/code\]', re.DOTALL | re.MULTILINE)
    code_re2 = re.compile(r'\[sourcecode.* lang.*?="(.*?)?".*\](.*?)\[/sourcecode\]', re.DOTALL | re.MULTILINE)
    code_re3 = re.compile(r'\[code.*?\](.*?)\[/code\]', re.DOTALL | re.MULTILINE)
    code_re4 = re.compile(r'\[sourcecode.*?\](.*?)\[/sourcecode\]', re.DOTALL | re.MULTILINE)

    def transform_code(self, content):
        """Transform code blocks."""
        # https://en.support.wordpress.com/code/posting-source-code/. There are
        # a ton of things not supported here. We only do a basic [code
        # lang="x"] -> ```x translation, and remove quoted html entities (<,
        # >, &, and ").
        def replacement(m, c=content):
            if len(m.groups()) == 1:
                language = ''
                code = m.group(0)
            else:
                language = m.group(1) or ''
                code = m.group(2)
            code = code.replace('&amp;', '&')
            code = code.replace('&gt;', '>')
            code = code.replace('&lt;', '<')
            code = code.replace('&quot;', '"')
            return '```{language}\n{code}\n```'.format(language=language, code=code)

        content = self.code_re1.sub(replacement, content)
        content = self.code_re2.sub(replacement, content)
        content = self.code_re3.sub(replacement, content)
        content = self.code_re4.sub(replacement, content)
        return content

    @staticmethod
    def transform_caption(content, use_html=False):
        """Transform captions."""
        new_caption = re.sub(r'\[/caption\]', '</h1>' if use_html else '', content)
        new_caption = re.sub(r'\[caption.*\]', '<h1>' if use_html else '', new_caption)

        return new_caption

    def transform_multiple_newlines(self, content):
        """Replace multiple newlines with only two."""
        if self.squash_newlines:
            return re.sub(r'\n{3,}', r'\n\n', content)
        else:
            return content

    def transform_content(self, content, post_format, attachments):
        """Transform content into appropriate format."""
        if post_format == 'wp':
            if self.transform_to_html:
                additional_data = {}
                if attachments is not None:
                    additional_data['attachments'] = attachments
                try:
                    content = self.wordpress_page_compiler.compile_to_string(content, additional_data=additional_data)
                except TypeError:  # old versions of the plugin don't support the additional argument
                    content = self.wordpress_page_compiler.compile_to_string(content)
                return content, 'html', True
            elif self.transform_to_markdown:
                # First convert to HTML with WordPress plugin
                additional_data = {}
                if attachments is not None:
                    additional_data['attachments'] = attachments
                try:
                    content = self.wordpress_page_compiler.compile_to_string(content, additional_data=additional_data)
                except TypeError:  # old versions of the plugin don't support the additional argument
                    content = self.wordpress_page_compiler.compile_to_string(content)
                # Now convert to MarkDown with html2text
                h = html2text.HTML2Text()
                content = h.handle(content)
                return content, 'md', False
            elif self.html2text:
                # TODO: what to do with [code] blocks?
                # content = self.transform_code(content)
                content = self.transform_caption(content, use_html=True)
                h = html2text.HTML2Text()
                content = h.handle(content)
                return content, 'md', False
            elif self.use_wordpress_compiler:
                return content, 'wp', False
            else:
                content = self.transform_code(content)
                content = self.transform_caption(content)
                content = self.transform_multiple_newlines(content)
                return content, 'md', True
        elif post_format == 'markdown':
            return content, 'md', True
        elif post_format == 'none':
            return content, 'html', True
        else:
            return None

    def _extract_comment(self, comment, wordpress_namespace):
        """Extract comment from dump."""
        id = int(get_text_tag(comment, "{{{0}}}comment_id".format(wordpress_namespace), None))
        author = get_text_tag(comment, "{{{0}}}comment_author".format(wordpress_namespace), None)
        author_email = get_text_tag(comment, "{{{0}}}comment_author_email".format(wordpress_namespace), None)
        author_url = get_text_tag(comment, "{{{0}}}comment_author_url".format(wordpress_namespace), None)
        author_IP = get_text_tag(comment, "{{{0}}}comment_author_IP".format(wordpress_namespace), None)
        # date = get_text_tag(comment, "{{{0}}}comment_date".format(wordpress_namespace), None)
        date_gmt = get_text_tag(comment, "{{{0}}}comment_date_gmt".format(wordpress_namespace), None)
        content = get_text_tag(comment, "{{{0}}}comment_content".format(wordpress_namespace), None)
        approved = get_text_tag(comment, "{{{0}}}comment_approved".format(wordpress_namespace), '0')
        if approved == '0':
            approved = 'hold'
        elif approved == '1':
            approved = 'approved'
        elif approved == 'spam' or approved == 'trash':
            pass
        else:
            LOGGER.warn("Unknown comment approved status: {0}".format(approved))
        parent = int(get_text_tag(comment, "{{{0}}}comment_parent".format(wordpress_namespace), 0))
        if parent == 0:
            parent = None
        user_id = int(get_text_tag(comment, "{{{0}}}comment_user_id".format(wordpress_namespace), 0))
        if user_id == 0:
            user_id = None

        if approved == 'trash' or approved == 'spam':
            return None

        return {"id": id, "status": str(approved), "approved": approved == "approved",
                "author": author, "email": author_email, "url": author_url, "ip": author_IP,
                "date": date_gmt, "content": content, "parent": parent, "user_id": user_id}

    def _write_comment(self, filename, comment):
        """Write comment to file."""
        def write_header_line(fd, header_field, header_content):
            """Write comment header line."""
            if header_content is None:
                return
            header_content = unicode_str(header_content).replace('\n', ' ')
            line = '.. ' + header_field + ': ' + header_content + '\n'
            fd.write(line.encode('utf8'))

        with open(filename, "wb+") as fd:
            write_header_line(fd, "id", comment["id"])
            write_header_line(fd, "status", comment["status"])
            write_header_line(fd, "approved", comment["approved"])
            write_header_line(fd, "author", comment["author"])
            write_header_line(fd, "author_email", comment["email"])
            write_header_line(fd, "author_url", comment["url"])
            write_header_line(fd, "author_IP", comment["ip"])
            write_header_line(fd, "date_utc", comment["date"])
            write_header_line(fd, "parent_id", comment["parent"])
            write_header_line(fd, "wordpress_user_id", comment["user_id"])
            fd.write(('\n' + comment['content']).encode('utf8'))

    def _create_metadata(self, status, excerpt, tags, categories, post_name=None):
        """Create post metadata."""
        other_meta = {'wp-status': status}
        if excerpt is not None:
            other_meta['excerpt'] = excerpt
        if self.export_categories_as_categories:
            cats = []
            for text in categories:
                if text in self._category_paths:
                    cats.append(self._category_paths[text])
                else:
                    cats.append(utils.join_hierarchical_category_path([text]))
            other_meta['categories'] = ','.join(cats)
            if len(cats) > 0:
                other_meta['category'] = cats[0]
                if len(cats) > 1:
                    LOGGER.warn(('Post "{0}" has more than one category! ' +
                                 'Will only use the first one.').format(post_name))
            tags_cats = tags
        else:
            tags_cats = tags + categories
        return tags_cats, other_meta

    _tag_sanitize_map = {True: {}, False: {}}

    def _sanitize(self, tag, is_category):
        if self.tag_saniziting_strategy == 'lower':
            return tag.lower()
        if tag.lower() not in self._tag_sanitize_map[is_category]:
            self._tag_sanitize_map[is_category][tag.lower()] = [tag]
            return tag
        previous = self._tag_sanitize_map[is_category][tag.lower()]
        if self.tag_saniziting_strategy == 'first':
            if tag != previous[0]:
                LOGGER.warn("Changing spelling of {0} name '{1}' to {2}.".format('category' if is_category else 'tag', tag, previous[0]))
            return previous[0]
        else:
            LOGGER.error("Unknown tag sanitizing strategy '{0}'!".format(self.tag_saniziting_strategy))
            sys.exit(1)
        return tag

    def import_postpage_item(self, item, wordpress_namespace, out_folder=None, attachments=None):
        """Take an item from the feed and creates a post file."""
        if out_folder is None:
            out_folder = 'posts'

        title = get_text_tag(item, 'title', 'NO TITLE')

        # titles can have line breaks in them, particularly when they are
        # created by third-party tools that post to Wordpress.
        # Handle windows-style and unix-style line endings.
        title = title.replace('\r\n', ' ').replace('\n', ' ')

        # link is something like http://foo.com/2012/09/01/hello-world/
        # So, take the path, utils.slugify it, and that's our slug
        link = get_text_tag(item, 'link', None)
        parsed = urlparse(link)
        path = unquote(parsed.path.strip('/'))

        try:
            if isinstance(path, utils.bytes_str):
                path = path.decode('utf8', 'replace')
            else:
                path = path
        except AttributeError:
            pass

        # Cut out the base directory.
        if path.startswith(self.base_dir.strip('/')):
            path = path.replace(self.base_dir.strip('/'), '', 1)

        pathlist = path.split('/')
        if parsed.query:  # if there are no nice URLs and query strings are used
            out_folder = os.path.join(*([out_folder] + pathlist))
            slug = get_text_tag(
                item, '{{{0}}}post_name'.format(wordpress_namespace), None)
            if not slug:  # it *may* happen
                slug = get_text_tag(
                    item, '{{{0}}}post_id'.format(wordpress_namespace), None)
            if not slug:  # should never happen
                LOGGER.error("Error converting post:", title)
                return False
        else:
            if len(pathlist) > 1:
                out_folder = os.path.join(*([out_folder] + pathlist[:-1]))
            slug = utils.slugify(pathlist[-1], self.lang)

        description = get_text_tag(item, 'description', '')
        post_date = get_text_tag(
            item, '{{{0}}}post_date'.format(wordpress_namespace), None)
        try:
            dt = utils.to_datetime(post_date)
        except ValueError:
            dt = datetime.datetime(1970, 1, 1, 0, 0, 0)
            LOGGER.error('Malformed date "{0}" in "{1}" [{2}], assuming 1970-01-01 00:00:00 instead.'.format(post_date, title, slug))
            post_date = dt.strftime('%Y-%m-%d %H:%M:%S')

        if dt.tzinfo and self.timezone is None:
            self.timezone = utils.get_tzname(dt)
        status = get_text_tag(
            item, '{{{0}}}status'.format(wordpress_namespace), 'publish')
        content = get_text_tag(
            item, '{http://purl.org/rss/1.0/modules/content/}encoded', '')
        excerpt = get_text_tag(
            item, '{http://wordpress.org/export/1.2/excerpt/}encoded', None)

        if excerpt is not None:
            if len(excerpt) == 0:
                excerpt = None

        tags = []
        categories = []
        if status == 'trash':
            LOGGER.warn('Trashed post "{0}" will not be imported.'.format(title))
            return False
        elif status == 'private':
            tags.append('private')
            is_draft = False
            is_private = True
        elif status != 'publish':
            tags.append('draft')
            is_draft = True
            is_private = False
        else:
            is_draft = False
            is_private = False

        for tag in item.findall('category'):
            text = tag.text
            type = 'category'
            if 'domain' in tag.attrib:
                type = tag.attrib['domain']
            if text == 'Uncategorized' and type == 'category':
                continue
            if type == 'category':
                categories.append(text)
            else:
                tags.append(text)

        if '$latex' in content:
            tags.append('mathjax')

        for i, cat in enumerate(categories[:]):
            cat = self._sanitize(cat, True)
            categories[i] = cat
            self.all_tags.add(cat)

        for i, tag in enumerate(tags[:]):
            tag = self._sanitize(tag, False)
            tags[i] = tag
            self.all_tags.add(tag)

        # Find post format if it's there
        post_format = 'wp'
        format_tag = [x for x in item.findall('*//{%s}meta_key' % wordpress_namespace) if x.text == '_tc_post_format']
        if format_tag:
            post_format = format_tag[0].getparent().find('{%s}meta_value' % wordpress_namespace).text
            if post_format == 'wpautop':
                post_format = 'wp'

        if is_draft and self.exclude_drafts:
            LOGGER.notice('Draft "{0}" will not be imported.'.format(title))
            return False
        elif is_private and self.exclude_privates:
            LOGGER.notice('Private post "{0}" will not be imported.'.format(title))
            return False
        elif content.strip() or self.import_empty_items:
            # If no content is found, no files are written.
            self.url_map[link] = (self.context['SITE_URL'] +
                                  out_folder.rstrip('/') + '/' + slug +
                                  '.html').replace(os.sep, '/')
            if hasattr(self, "separate_qtranslate_content") \
               and self.separate_qtranslate_content:
                content_translations = separate_qtranslate_content(content)
            else:
                content_translations = {"": content}
            default_language = self.context["DEFAULT_LANG"]
            for lang, content in content_translations.items():
                try:
                    content, extension, rewrite_html = self.transform_content(content, post_format, attachments)
                except:
                    LOGGER.error(('Cannot interpret post "{0}" (language {1}) with post ' +
                                  'format {2}!').format(os.path.join(out_folder, slug), lang, post_format))
                    return False
                if lang:
                    out_meta_filename = slug + '.meta'
                    if lang == default_language:
                        out_content_filename = slug + '.' + extension
                    else:
                        out_content_filename \
                            = utils.get_translation_candidate(self.context,
                                                              slug + "." + extension, lang)
                        self.extra_languages.add(lang)
                    meta_slug = slug
                else:
                    out_meta_filename = slug + '.meta'
                    out_content_filename = slug + '.' + extension
                    meta_slug = slug
                tags, other_meta = self._create_metadata(status, excerpt, tags, categories,
                                                         post_name=os.path.join(out_folder, slug))

                meta = {
                    "title": title,
                    "slug": meta_slug,
                    "date": post_date,
                    "description": description,
                    "tags": ','.join(tags),
                }
                meta.update(other_meta)
                if self.onefile:
                    self.write_post(
                        os.path.join(self.output_folder,
                                     out_folder, out_content_filename),
                        content,
                        meta,
                        self._get_compiler(),
                        rewrite_html)
                else:
                    self.write_metadata(os.path.join(self.output_folder, out_folder,
                                                     out_meta_filename),
                                        title, meta_slug, post_date, description, tags, **other_meta)
                    self.write_content(
                        os.path.join(self.output_folder,
                                     out_folder, out_content_filename),
                        content,
                        rewrite_html)

            if self.export_comments:
                comments = []
                for tag in item.findall('{{{0}}}comment'.format(wordpress_namespace)):
                    comment = self._extract_comment(tag, wordpress_namespace)
                    if comment is not None:
                        comments.append(comment)

                for comment in comments:
                    comment_filename = "{0}.{1}.wpcomment".format(slug, comment['id'])
                    self._write_comment(os.path.join(self.output_folder, out_folder, comment_filename), comment)

            return (out_folder, slug)
        else:
            LOGGER.warn(('Not going to import "{0}" because it seems to contain'
                         ' no content.').format(title))
            return False

    def _extract_item_info(self, item):
        """Extract information about an item."""
        # The namespace usually is something like:
        # http://wordpress.org/export/1.2/
        wordpress_namespace = item.nsmap['wp']
        post_type = get_text_tag(
            item, '{{{0}}}post_type'.format(wordpress_namespace), 'post')
        post_id = int(get_text_tag(
            item, '{{{0}}}post_id'.format(wordpress_namespace), "0"))
        parent_id = get_text_tag(
            item, '{{{0}}}post_parent'.format(wordpress_namespace), None)
        return wordpress_namespace, post_type, post_id, parent_id

    def process_item_if_attachment(self, item):
        """Process attachments."""
        wordpress_namespace, post_type, post_id, parent_id = self._extract_item_info(item)

        if post_type == 'attachment':
            data = self.import_attachment(item, wordpress_namespace)
            # If parent was found, store relation with imported files
            if parent_id is not None and int(parent_id) != 0:
                self.attachments[int(parent_id)][post_id] = data
            else:
                LOGGER.warn("Attachment #{0} ({1}) has no parent!".format(post_id, data['files']))

    def write_attachments_info(self, path, attachments):
        """Write attachments info file."""
        with io.open(path, "wb") as file:
            file.write(json.dumps(attachments).encode('utf-8'))

    def process_item_if_post_or_page(self, item):
        """Process posts and pages."""
        wordpress_namespace, post_type, post_id, parent_id = self._extract_item_info(item)

        if post_type != 'attachment':
            # Get attachments for post
            attachments = self.attachments.pop(post_id, None)
            # Import item
            if post_type == 'post':
                out_folder_slug = self.import_postpage_item(item, wordpress_namespace, 'posts', attachments)
            else:
                out_folder_slug = self.import_postpage_item(item, wordpress_namespace, 'pages', attachments)
            # Process attachment data
            if attachments is not None:
                # If post was exported, store data
                if out_folder_slug:
                    destination = os.path.join(self.output_folder, out_folder_slug[0],
                                               out_folder_slug[1] + ".attachments.json")
                    self.write_attachments_info(destination, attachments)

    def import_posts(self, channel):
        """Import posts into the site."""
        self.attachments = defaultdict(dict)
        # First process attachments
        for item in channel.findall('item'):
            self.process_item_if_attachment(item)
        # Next process posts
        for item in channel.findall('item'):
            self.process_item_if_post_or_page(item)
        # Assign attachments to posts
        for post_id in self.attachments:
            LOGGER.warn(("Found attachments for post or page #{0}, but didn't find post or page. " +
                         "(Attachments: {1})").format(post_id, [e['files'][0] for e in self.attachments[post_id].values()]))


def get_text_tag(tag, name, default):
    """Get the text of an XML tag."""
    if tag is None:
        return default
    t = tag.find(name)
    if t is not None and t.text is not None:
        return t.text
    else:
        return default


def separate_qtranslate_content(text):
    """Parse the content of a wordpress post or page and separate qtranslate languages.

    qtranslate tags: <!--:LL-->blabla<!--:-->
    """
    # TODO: uniformize qtranslate tags <!--/en--> => <!--:-->
    qt_start = "<!--:"
    qt_end = "-->"
    qt_end_with_lang_len = 5
    qt_chunks = text.split(qt_start)
    content_by_lang = {}
    common_txt_list = []
    for c in qt_chunks:
        if not c.strip():
            continue
        if c.startswith(qt_end):
            # just after the end of a language specific section, there may
            # be some piece of common text or tags, or just nothing
            lang = ""  # default language
            c = c.lstrip(qt_end)
            if not c:
                continue
        elif c[2:].startswith(qt_end):
            # a language specific section (with language code at the begining)
            lang = c[:2]
            c = c[qt_end_with_lang_len:]
        else:
            # nowhere specific (maybe there is no language section in the
            # currently parsed content)
            lang = ""  # default language
        if not lang:
            common_txt_list.append(c)
            for l in content_by_lang.keys():
                content_by_lang[l].append(c)
        else:
            content_by_lang[lang] = content_by_lang.get(lang, common_txt_list) + [c]
    # in case there was no language specific section, just add the text
    if common_txt_list and not content_by_lang:
        content_by_lang[""] = common_txt_list
    # Format back the list to simple text
    for l in content_by_lang.keys():
        content_by_lang[l] = " ".join(content_by_lang[l])
    return content_by_lang
