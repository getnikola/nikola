from yapsy.IPlugin import IPlugin

__all__ = ['PageCompiler', 'Task', 'TemplateSystem']

class Task(object):
    """PLugins of this type are task generators."""

    name = "dummy_task"

    # default tasks are executed by default.
    # the others have to be specifie in the command line.
    is_default = True

    def set_site(self, site):
        """Sets site, which is a Nikola instance."""
        self.site = site

    def gen_tasks(self):
        """Task generator."""
        raise Exception("Implement Me First")


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
