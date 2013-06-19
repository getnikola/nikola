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

__all__ = [
    'Command',
    'LateTask',
    'PageCompiler',
    'Task',
    'TemplateSystem'
]

from yapsy.IPlugin import IPlugin
from doit.cmd_base import Command as DoitCommand


class BasePlugin(IPlugin):
    """Base plugin class."""

    def set_site(self, site):
        """Sets site, which is a Nikola instance."""
        self.site = site


class Command(BasePlugin, DoitCommand):
    """These plugins are exposed via the command line.
    They implement the doit Command interface."""

    name = "dummy_command"

    doc_purpose = "A short explanation."
    doc_usage = ""
    doc_description = None  # None value will completely ommit line from doc
    # see http://python-doit.sourceforge.net/cmd_run.html#parameters
    cmd_options = ()
    needs_config = True

    def __init__(self, *args, **kwargs):
        BasePlugin.__init__(self, *args, **kwargs)
        DoitCommand.__init__(self)

    def execute(self, options={}, args=[]):
        """Check if the command can run in the current environment,
        fail if needed, or call _execute."""
        if self.needs_config and not self.site.configured:
            print("This command needs to run inside an existing Nikola site.")
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
    for opt in self.options:
        text.extend(opt.help_doc())

    if self.doc_description is not None:
        text.append("")
        text.append("Description:")
        text.append(self.doc_description)
    return "\n".join(text)

DoitCommand.help = help


class BaseTask(BasePlugin):
    """PLugins of this type are task generators."""

    name = "dummy_task"

    # default tasks are executed by default.
    # the others have to be specifie in the command line.
    is_default = True

    def gen_tasks(self):
        """Task generator."""
        raise NotImplementedError()


class Task(BaseTask):
    """PLugins of this type are task generators."""


class LateTask(BaseTask):
    """Plugins of this type are executed after all plugins of type Task."""

    name = "dummy_latetask"


class TemplateSystem(BasePlugin):
    """Plugins of this type wrap templating systems."""

    name = "dummy templates"

    def set_directories(self, directories, cache_folder):
        """Sets the list of folders where templates are located and cache."""
        raise NotImplementedError()

    def template_deps(self, template_name):
        """Returns filenames which are dependencies for a template."""
        raise NotImplementedError()

    def render_template(name, output_name, context):
        """Renders template to a file using context.

        This must save the data to output_name *and* return it
        so that the caller may do additional processing.
        """
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
    default_metadata = {
        'title': '',
        'slug': '',
        'date': '',
        'tags': '',
        'link': '',
        'description': '',
    }

    def compile_html(self, source, dest, is_two_file=False):
        """Compile the source, save it on dest."""
        raise NotImplementedError()

    def create_post(self, path, onefile=False, **kw):
        """Create post file with optional metadata."""
        raise NotImplementedError()

    def extension(self):
        """The preferred extension for the output of this compiler."""
        return ".html"


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
