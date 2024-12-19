import pathlib
import socket
from typing import Dict, Any

from ..helper import FakeSite
from nikola.utils import get_logger

SERVER_ADDRESS = "localhost"
TEST_MAX_DURATION = 10  # Watchdog: Give up the test if it did not succeed during this time span.

# Folder that has the fixture file we expect the server to serve:
OUTPUT_FOLDER = pathlib.Path(__file__).parent.parent / "data" / "dev_server_sample_output_folder"

LOGGER = get_logger("test_dev_server")


def find_unused_port() -> int:
    """Ask the OS for a currently unused port number.

    (More precisely, a port that can be used for a TCP server servicing SERVER_ADDRESS.)
    We use a method here rather than a fixture to minimize side effects of failing tests.
    """
    s = socket.socket()
    try:
        ANY_PORT = 0
        s.bind((SERVER_ADDRESS, ANY_PORT))
        address, port = s.getsockname()
        LOGGER.info("Trying to set up dev server on http://%s:%i/", address, port)
        return port
    finally:
        s.close()


class MyFakeSite(FakeSite):
    def __init__(self, config: Dict[str, Any], configuration_filename="conf.py"):
        super(MyFakeSite, self).__init__()
        self.configured = True
        self.debug = True
        self.THEMES = []
        self._plugin_places = []
        self.registered_auto_watched_folders = set()
        self.config = config
        self.configuration_filename = configuration_filename
