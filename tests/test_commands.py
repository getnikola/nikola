# -*- coding: utf-8 -*-

from nikola.plugins.command.version import CommandVersion


def test_version():
    """Test `nikola version`."""
    CommandVersion().execute()
