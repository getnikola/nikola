#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Please don't edit this file unless you really know what you are doing.
# The configuration is now in conf.py

from doit.reporter import ExecutedOnlyReporter

from nikola.nikola import Nikola

import conf

DOIT_CONFIG = {
        'reporter': ExecutedOnlyReporter,
        'default_tasks': ['render_site'],
}
SITE = Nikola(**conf.__dict__)


def task_render_site():
    return SITE.gen_tasks()
