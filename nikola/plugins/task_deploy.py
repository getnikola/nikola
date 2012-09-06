import os

from nikola.plugin_categories import Task
from nikola import utils

class Deploy(Task):
    """Deploy site.  """
    name = "deploy"
    is_default = False

    def gen_tasks(self):
        yield {
            "basename": self.name,
            "actions": self.site.config['DEPLOY_COMMANDS'],
            "verbosity": 2,
        }
