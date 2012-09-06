from yapsy import IPlugin

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
        print "This needs reimplementing."
        yield {
            'basename': self.name,
            'actions': [],
	}
