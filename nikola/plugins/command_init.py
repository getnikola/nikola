# Copyright (c) 2012 Roberto Alsina y otros.

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

from __future__ import print_function
import os
import shutil
import codecs

from mako.template import Template

import nikola
from nikola.plugin_categories import Command


class CommandInit(Command):
    """Create a new site."""

    name = "init"

    doc_usage = "[--demo] folder"
    needs_config = False
    doc_purpose = """Create a Nikola site in the specified folder."""
    cmd_options = [
        {
            'name': 'demo',
            'long': 'demo',
            'default': False,
            'type': bool,
            'help': "Create a site filled with example data.",
        },
        {
            'name': 'install_extra_plugin',
            'long': 'install_extra_plugin',
            'default': None,
            'type': str,
            'help': "Specify an additional plugin to install.",
        },
        {
            'name': 'list_extra_plugins',
            'long': 'list_extra_plugins',
            'default': False,
            'type': bool,
            'help': "List available extra plugins.",
        },
    ]

    SAMPLE_CONF = {
        'BLOG_AUTHOR': "Your Name",
        'BLOG_TITLE': "Demo Site",
        'SITE_URL': "http://nikola.ralsina.com.ar",
        'BLOG_EMAIL': "joe@demo.site",
        'BLOG_DESCRIPTION': "This is a demo site for Nikola.",
        'DEFAULT_LANG': "en",

        'POST_PAGES': """(
    ("posts/*.txt", "posts", "post.tmpl", True),
    ("stories/*.txt", "stories", "story.tmpl", False),
)""",

        'POST_COMPILERS': """{
    "rest": ('.txt', '.rst'),
    "markdown": ('.md', '.mdown', '.markdown'),
    "textile": ('.textile',),
    "txt2tags": ('.t2t',),
    "bbcode": ('.bb',),
    "wiki": ('.wiki',),
    "ipynb": ('.ipynb',),
    "html": ('.html', '.htm')
}""",
        'REDIRECTIONS': '[]',
    }

    @staticmethod
    def get_path_to_nikola_modules():
        return os.path.dirname(nikola.__file__)

    @classmethod
    def get_path_to_extra_plugins(cls):
        return os.path.join(cls.get_path_to_nikola_modules(), 'extra_plugins')

    @classmethod
    def list_extra_plugins(cls):
        plugin_files = [name for name in os.listdir(cls.get_path_to_extra_plugins())
                        if name.endswith('.plugin')]

        print('The following extra plugins are available:')
        for plugin_file in plugin_files:
            print(' - {0}'.format(plugin_file[:-7]))

    @classmethod
    def copy_sample_site(cls, target):
        lib_path = cls.get_path_to_nikola_modules()
        src = os.path.join(lib_path, 'data', 'samplesite')
        shutil.copytree(src, target)

    @classmethod
    def create_configuration(cls, target):
        lib_path = cls.get_path_to_nikola_modules()
        template_path = os.path.join(lib_path, 'conf.py.in')
        conf_template = Template(filename=template_path)
        conf_path = os.path.join(target, 'conf.py')
        with codecs.open(conf_path, 'w+', 'utf8') as fd:
            fd.write(conf_template.render(**cls.SAMPLE_CONF))

    @classmethod
    def create_empty_site(cls, target):
        for folder in ('files', 'galleries', 'listings', 'posts', 'stories'):
            os.makedirs(os.path.join(target, folder))

    @classmethod
    def install_plugin(cls, target, plugin_name):
        target_plugin_directory = os.path.join(target, 'plugins')
        if not os.path.exists(target_plugin_directory):
            os.makedirs(target_plugin_directory)

        nikola_source = cls.get_path_to_nikola_modules()
        source_extra_plugin_directory = os.path.join(
            nikola_source, 'extra_plugins')
        assert os.path.exists(
            source_extra_plugin_directory), 'Missing folder extra_plugins'

        source_plugin_information = os.path.join(
            source_extra_plugin_directory, plugin_name + '.plugin')
        assert os.path.exists(source_extra_plugin_directory), 'Missing plugin information file for plugin "{0}".'.format(
            source_plugin_information)

        source_plugin_directory = os.path.join(
            source_extra_plugin_directory, plugin_name)
        source_plugin_file = os.path.join(
            source_extra_plugin_directory, plugin_name + '.py')
        if os.path.isfile(source_plugin_file):
            shutil.copyfile(source_plugin_information, os.path.join(
                target_plugin_directory, plugin_name + '.plugin'))
            shutil.copyfile(source_plugin_file, os.path.join(
                target_plugin_directory, plugin_name + '.py'))
        if os.path.isdir(source_plugin_directory):
            shutil.copyfile(source_plugin_information, os.path.join(
                target_plugin_directory, plugin_name + '.plugin'))
            shutil.copytree(source_plugin_directory, os.path.join(
                target_plugin_directory, plugin_name))
        else:
            raise OSError(
                'Plugin {0} not found. Did you spell it correctly?'.format(plugin_name))

    def _execute(self, options={}, args=None):
        """Create a new site."""
        if options.get('list_extra_plugins', False):
            self.list_extra_plugins()
            return

        if not args:
            print("Usage: nikola init [options] folder")
            return False

        target = args[0]
        if target is None:
            print(self.usage)
        else:
            if not options or not options.get('demo'):
                self.create_empty_site(target)
                print('Created empty site at {0}.'.format(target))
            else:
                self.copy_sample_site(target)
                print("A new site with example data has been created at "
                      "{0}.".format(target))
                print("See README.txt in that folder for more information.")

            self.create_configuration(target)

            if options and options.get('install_extra_plugin'):
                self.install_plugin(target, options['install_extra_plugin'])
