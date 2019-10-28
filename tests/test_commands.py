from nikola.plugins.command.version import CommandVersion


def test_command_version():
    """Test `nikola version`."""
    CommandVersion().execute()
