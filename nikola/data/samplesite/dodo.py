#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Please don't edit this file unless you really know what you are doing.
# The configuration is now in conf.py

import os

from doit.reporter import ExecutedOnlyReporter

from nikola.nikola import Nikola

import conf

DOIT_CONFIG = {
        'reporter': ExecutedOnlyReporter,
        'default_tasks': ['render_site'],
}
site = Nikola(**conf.__dict__)
def task_render_site():
    return site.gen_tasks()
    
if __name__ == "__main__":
    _nikola_main()
