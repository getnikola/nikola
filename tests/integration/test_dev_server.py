import asyncio
import nikola.plugins.command.auto as auto
from nikola.utils import get_logger
import pytest
import pathlib
import socket
from typing import Optional
import requests

from ..helper import FakeSite

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


def test_serves_root_dir(site, expected_text) -> None:
    command_auto = auto.CommandAuto()
    command_auto.set_site(site)
    options = {
        "browser": False,
        "ipv6": False,
        "address": SERVER_ADDRESS,
        "port": find_unused_port(),
        "db-file": "/dev/null",
        "backend": "No backend",
        "no-server": False
    }

    # We start an event loop, run the test in an executor,
    # and wait for the event loop to terminate.
    # These variables help to transport the test result to
    # the main thread outside the event loop:
    test_was_successful = False
    test_problem_description = "Async test setup apparently broken"
    test_inner_error: Optional[BaseException] = None

    async def grab_loop_and_run_test() -> None:
        loop = asyncio.get_running_loop()
        watchdog_handle = loop.call_later(TEST_MAX_DURATION, lambda: loop.stop())
        nonlocal test_problem_description
        test_problem_description = f"Test did not complete within {TEST_MAX_DURATION} seconds."

        def run_test() -> None:
            nonlocal test_was_successful, test_problem_description, test_inner_error
            try:
                with requests.Session() as session:
                    # First subtest: Grab the document root index.html file:
                    server_base_uri = f"http://{options['address']}:{options['port']}/"
                    res = session.get(server_base_uri)
                    res.raise_for_status()
                    assert "text/html; charset=utf-8" == res.headers['content-type']
                    assert expected_text in res.text

                    # Second subtest: Does the dev server serve something for the livereload JS?
                    res_js = session.get(f"{server_base_uri}livereload.js?snipver=1")
                    res_js.raise_for_status()
                    content_type_js = res_js.headers['content-type']
                    assert "javascript" in content_type_js

                test_was_successful = True
                test_problem_description = "No problem. All is well."
            except BaseException as be:
                test_inner_error = be
            finally:
                LOGGER.info("Test completed, %s: %s",
                            "successfully" if test_was_successful else "failing",
                            test_problem_description)
                loop.call_soon_threadsafe(lambda: watchdog_handle.cancel())

                # We give the outer grab_loop_and_run_test a chance to complete
                # before burning the bridge:
                loop.call_soon_threadsafe(lambda: loop.call_later(0.05, lambda: loop.stop()))
        await loop.run_in_executor(None, run_test)

    # We defeat the nikola site building functionality, so this does not actually get called.
    # But the setup code sets this up and needs a command list for that.
    command_auto.nikola_cmd = ["echo"]

    # Defeat the site building functionality, and instead insert the test:
    command_auto.run_initial_rebuild = grab_loop_and_run_test

    # Start the development server
    # which under the hood runs our test when trying to build the site:
    command_auto.execute(options=options)

    # Verify the test succeeded:
    if test_inner_error is not None:
        raise test_inner_error
    assert test_was_successful, test_problem_description


class MyFakeSite(FakeSite):
    def __init__(self, config, configuration_filename):
        self.configured = True
        self.debug = True
        self.THEMES = []
        self._plugin_places = []
        self.registered_auto_watched_folders = set()
        self.config = config
        self.configuration_filename = configuration_filename


@pytest.fixture(scope="module")
def site() -> MyFakeSite:
    assert OUTPUT_FOLDER.is_dir(), \
        f"Could not find dev server test fixture {OUTPUT_FOLDER.as_posix()}"

    config = {
        "post_pages": [],
        "FILES_FOLDERS": [],
        "GALLERY_FOLDERS": [],
        "LISTINGS_FOLDERS": [],
        "IMAGE_FOLDERS": [],
        "OUTPUT_FOLDER": OUTPUT_FOLDER.as_posix(),
    }
    return MyFakeSite(config, "conf.py")


@pytest.fixture(scope="module")
def expected_text():
    """Read the index.html file from the fixture folder and return most of it.

    For life reload, the server will fiddle with HTML <head>,
    so this only returns everything after the opening <body> tag.
    """
    with open(OUTPUT_FOLDER / "index.html", encoding="utf-8") as html_file:
        all_html = html_file.read()
        return all_html[all_html.find("<body>"):]
