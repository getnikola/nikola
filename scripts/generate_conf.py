#!/usr/bin/env python
"""Generate a conf.py file from the template, using default settings."""

import nikola.plugins.command.init

try:
    print(nikola.plugins.command.init.CommandInit.create_configuration_to_string())
except:
    print(nikola.plugins.command.init.CommandInit.create_configuration_to_string().encode('utf-8'))
