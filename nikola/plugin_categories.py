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


class BasePlugin(IPlugin):
    """Base plugin class."""

    def set_site(self, site):
        """Sets site, which is a Nikola instance."""
        self.site = site


class Command(BasePlugin):
    """These plugins are exposed via the command line."""

    name = "dummy_command"

    short_help = "A short explanation."

    def run(self):
        """Do whatever this command does."""
        raise Exception("Implement Me First")


class BaseTask(BasePlugin):
    """PLugins of this type are task generators."""

    name = "dummy_task"

    # default tasks are executed by default.
    # the others have to be specifie in the command line.
    is_default = True

    def gen_tasks(self):
        """Task generator."""
        raise Exception("Implement Me First")


class Task(BaseTask):
    """PLugins of this type are task generators."""


class LateTask(BaseTask):
    """Plugins of this type are executed after all plugins of type Task."""

    name = "dummy_latetask"


class TemplateSystem(object):
    """Plugins of this type wrap templating systems."""

    name = "dummy templates"

    def set_directories(self, directories, cache_folder):
        """Sets the list of folders where templates are located and cache."""
        raise Exception("Implement Me First")

    def template_deps(self, template_name):
        """Returns filenames which are dependencies for a template."""
        raise Exception("Implement Me First")

    def render_template(name, output_name, context):
        """Renders template to a file using context.

        This must save the data to output_name *and* return it
        so that the caller may do additional processing.
        """
        raise Exception("Implement Me First")


class PageCompiler(object):
    """Plugins that compile text files into HTML."""

    name = "dummy compiler"

    def compile_html(self, source, dest):
        """Compile the source, save it on dest."""
        raise Exception("Implement Me First")

    def create_post(self, path, onefile=False, title="", slug="", date="",
                    tags=""):
        """Create post file with optional metadata."""
        raise Exception("Implement Me First")
