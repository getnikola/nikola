"""
Simple plugin tests.

More advanced tests should be in a separate module.
"""


def test_command_version():
    """Test `nikola version`."""
    from nikola.plugins.command.version import CommandVersion

    CommandVersion().execute()


def test_importing_plugin_task_galleries():
    import nikola.plugins.task.galleries  # NOQA


def test_importing_plugin_compile_pandoc():
    import nikola.plugins.compile.pandoc  # NOQA
