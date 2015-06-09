# -*- coding: utf-8 -*-

# Copyright © 2012-2015 Roberto Alsina and others.

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

from __future__ import absolute_import
import sys
import os
import re

from yapsy.IPlugin import IPlugin
from doit.cmd_base import Command as DoitCommand

from .utils import LOGGER, first_line

__all__ = [
    'Command',
    'LateTask',
    'PageCompiler',
    'RestExtension',
    'MarkdownExtension',
    'Task',
    'TaskMultiplier',
    'TemplateSystem',
    'SignalHandler',
    'ConfigPlugin',
    'PostScanner',
]


class BasePlugin(IPlugin):
    """Base plugin class."""

    def set_site(self, site):
        """Sets site, which is a Nikola instance."""
        self.site = site
        self.inject_templates()

    def inject_templates(self):
        """If this plugin contains a 'templates' folder,
        then templates/mako or templates/jinja will be inserted very early in
        the theme chain."""

        try:
            # Sorry, found no other way to get this
            mod_path = sys.modules[self.__class__.__module__].__file__
            mod_dir = os.path.dirname(mod_path)
            tmpl_dir = os.path.join(
                mod_dir, 'templates', self.site.template_system.name
            )
            if os.path.isdir(tmpl_dir):
                # Inject tmpl_dir low in the theme chain
                self.site.template_system.inject_directory(tmpl_dir)
        except AttributeError:
            # In some cases, __builtin__ becomes the module of a plugin.
            # We couldn’t reproduce that, and really find the reason for this,
            # so let’s just ignore it and be done with it.
            pass

    def inject_dependency(self, target, dependency):
        """Add 'dependency' to the target task's task_deps"""
        self.site.injected_deps[target].append(dependency)


class PostScanner(BasePlugin):
    """The scan method of these plugins is called by Nikola.scan_posts."""

    def scan(self):
        """Creates a list of posts from some source. Returns a list of Post objects."""
        raise NotImplementedError()


class Command(BasePlugin, DoitCommand):
    """These plugins are exposed via the command line.
    They implement the doit Command interface."""

    name = "dummy_command"

    doc_purpose = "A short explanation."
    doc_usage = ""
    doc_description = None  # None value will completely omit line from doc
    # see http://python-doit.sourceforge.net/cmd_run.html#parameters
    cmd_options = ()
    needs_config = True

    def __init__(self, *args, **kwargs):
        BasePlugin.__init__(self, *args, **kwargs)
        DoitCommand.__init__(self)

    def __call__(self, config=None, **kwargs):
        self._doitargs = kwargs
        DoitCommand.__init__(self, config, **kwargs)
        return self

    def execute(self, options=None, args=None):
        """Check if the command can run in the current environment,
        fail if needed, or call _execute."""
        options = options or {}
        args = args or []

        if self.needs_config and not self.site.configured:
            LOGGER.error("This command needs to run inside an existing Nikola site.")
            return False
        self._execute(options, args)

    def _execute(self, options, args):
        """Do whatever this command does.
        @param options (dict) with values from cmd_options
        @param args (list) list of positional arguments
        """
        raise NotImplementedError()


def help(self):
    """return help text"""
    text = []
    text.append("Purpose: %s" % self.doc_purpose)
    text.append("Usage:   nikola %s %s" % (self.name, self.doc_usage))
    text.append('')

    text.append("Options:")
    for opt in self.cmdparser.options:
        text.extend(opt.help_doc())

    if self.doc_description is not None:
        text.append("")
        text.append("Description:")
        text.append(self.doc_description)
    return "\n".join(text)

DoitCommand.help = help


class BaseTask(BasePlugin):
    """Plugins of this type are task generators."""

    name = "dummy_task"

    # default tasks are executed by default.
    # the others have to be specifie in the command line.
    is_default = True

    def gen_tasks(self):
        """Task generator."""
        raise NotImplementedError()

    def group_task(self):
        """dict for group task"""
        return {
            'basename': self.name,
            'name': None,
            'doc': first_line(self.__doc__),
        }


class Task(BaseTask):
    """Plugins of this type are task generators."""

    name = "dummy_task"


class LateTask(BaseTask):
    """Plugins of this type are executed after all plugins of type Task."""

    name = "dummy_latetask"


class TemplateSystem(BasePlugin):
    """Plugins of this type wrap templating systems."""

    name = "dummy_templates"

    def set_directories(self, directories, cache_folder):
        """Sets the list of folders where templates are located and cache."""
        raise NotImplementedError()

    def template_deps(self, template_name):
        """Returns filenames which are dependencies for a template."""
        raise NotImplementedError()

    def render_template(self, template_name, output_name, context):
        """Renders template to a file using context.

        This must save the data to output_name *and* return it
        so that the caller may do additional processing.
        """
        raise NotImplementedError()

    def render_template_to_string(self, template, context):
        """Renders template to a string using context. """
        raise NotImplementedError()

    def inject_directory(self, directory):
        """Injects the directory with the lowest priority in the
        template search mechanism."""
        raise NotImplementedError()


class TaskMultiplier(BasePlugin):
    """Plugins that take a task and return *more* tasks."""

    name = "dummy multiplier"

    def process(self, task):
        """Examine task and create more tasks.
        Returns extra tasks only."""
        return []


class PageCompiler(BasePlugin):
    """Plugins that compile text files into HTML."""

    name = "dummy compiler"
    demote_headers = False
    supports_onefile = True
    default_metadata = {
        'title': '',
        'slug': '',
        'date': '',
        'tags': '',
        'category': '',
        'link': '',
        'description': '',
        'type': 'text',
    }
    config_dependencies = []

    def register_extra_dependencies(self, post):
        """Add additional dependencies to the post object.

        Current main use is the ReST page compiler, which puts extra
        dependencies into a .deb file."""
        pass

    def compile_html(self, source, dest, is_two_file=False):
        """Compile the source, save it on dest."""
        raise NotImplementedError()

    def create_post(self, path, content=None, onefile=False, is_page=False, **kw):
        """Create post file with optional metadata."""
        raise NotImplementedError()

    def extension(self):
        """The preferred extension for the output of this compiler."""
        return ".html"

    def read_metadata(self, post, file_metadata_regexp=None, unslugify_titles=False, lang=None):
        """
        Read the metadata from a post, and return a metadata dict
        """
        return {}

    def split_metadata(self, data):
        """Split data from metadata in the raw post content.

        This splits in the first empty line that is NOT at the beginning
        of the document."""
        split_result = re.split('(\n\n|\r\n\r\n)', data.lstrip(), maxsplit=1)
        if len(split_result) == 1:
            return '', split_result[0]
        # ['metadata', '\n\n', 'post content']
        return split_result[0], split_result[-1]


class RestExtension(BasePlugin):
    name = "dummy_rest_extension"


class MarkdownExtension(BasePlugin):
    name = "dummy_markdown_extension"


class SignalHandler(BasePlugin):
    name = "dummy_signal_handler"


class ConfigPlugin(BasePlugin):
    """A plugin that can edit config (or modify the site) on-the-fly."""
    name = "dummy_config_plugin"


class Importer(Command):
    """Basic structure for importing data into Nikola.

    The flow is:

    read_data
    preprocess_data
    parse_data
    generate_base_site
        populate_context
        create_config
    filter_data
    process_data

    process_data can branch into:

    import_story (may use import_file and save_post)
    import_post (may use import_file and save_post)
    import_attachment (may use import_file)

    Finally:

    write_urlmap
    """

    name = "dummy_importer"

    def _execute(self, options={}, args=[]):
        """Import the data into Nikola."""
        raise NotImplementedError()

    def generate_base_site(self, path):
        """Create the base site."""
        raise NotImplementedError()

    def populate_context(self):
        """Use data to fill context for configuration."""
        raise NotImplementedError()

    def create_config(self):
        """Use the context to create configuration."""
        raise NotImplementedError()

    def read_data(self, source):
        """Fetch data into self.data"""
        raise NotImplementedError()

    def preprocess_data(self):
        """Modify data if needed."""
        pass

    def parse_data(self):
        """Convert self.data into self.items"""
        raise NotImplementedError()

    def filter_data(self):
        """Remove data that's not to be imported."""
        pass

    def process_data(self):
        """Go through self.items and save them."""

    def import_story(self):
        """Create a story."""
        raise NotImplementedError()

    def import_post(self):
        """Create a post."""
        raise NotImplementedError()

    def import_attachment(self):
        """Create an attachment."""
        raise NotImplementedError()

    def import_file(self):
        """Import a file."""
        raise NotImplementedError()

    def save_post(self):
        """Save a post to disk."""
        raise NotImplementedError()
