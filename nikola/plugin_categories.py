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

    def set_directories(self, directories):
        """Sets the list of folders where templates are located."""
        raise Exception("Implement Me First")

    def template_deps(self, template_name):
        """Returns filenames which are dependencies for a template."""
        raise Exception("Implement Me First")

    def render_template(name, output_name, context, global_context):
        """Renders template to a file using contexts.

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
