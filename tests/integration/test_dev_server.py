import asyncio
import nikola.plugins.command.auto as auto
from nikola.utils import get_logger
import pytest
import pathlib
import requests
import socket
import sys
from typing import Optional, Tuple, Any, Dict

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


class MyFakeSite(FakeSite):
    def __init__(self, config: Dict[str, Any], configuration_filename="conf.py"):
        self.configured = True
        self.debug = True
        self.THEMES = []
        self._plugin_places = []
        self.registered_auto_watched_folders = set()
        self.config = config
        self.configuration_filename = configuration_filename


def test_serves_root_dir(
    site_and_base_path: Tuple[MyFakeSite, str], expected_text: str
) -> None:
    site, base_path = site_and_base_path
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
    loop_for_this_test = None

    async def grab_loop_and_run_test() -> None:
        nonlocal test_problem_description, loop_for_this_test

        loop_for_this_test = asyncio.get_running_loop()
        watchdog_handle = loop_for_this_test.call_later(TEST_MAX_DURATION, lambda: loop_for_this_test.stop())
        test_problem_description = f"Test did not complete within {TEST_MAX_DURATION} seconds."

        def run_test() -> None:
            nonlocal test_was_successful, test_problem_description, test_inner_error
            try:
                with requests.Session() as session:
                    server_root_uri = f"http://{options['address']}:{options['port']}"

                    # First subtest: Grab the document root index.html file:
                    server_base_uri = f"{server_root_uri}{base_path}"
                    LOGGER.info("Attempting to fetch HTML from %s", server_base_uri)
                    res = session.get(server_base_uri)
                    res.raise_for_status()
                    assert "text/html; charset=utf-8" == res.headers['content-type']
                    assert expected_text in res.text

                    # Second subtest: Does the dev server serve something for the livereload JS?
                    js_uri = f"{server_root_uri}/livereload.js?snipver=1"
                    LOGGER.info("Attempting to fetch JS from %s", js_uri)
                    res_js = session.get(js_uri)
                    res_js.raise_for_status()
                    content_type_js = res_js.headers['content-type']
                    assert "javascript" in content_type_js

                test_was_successful = True
                test_problem_description = "No problem. All is well."
            except BaseException as be:
                LOGGER.error("Could not receive HTTP as expected.", exc_info=True)
                test_inner_error = be
                test_was_successful = False
                test_problem_description = "(see exception)"
            finally:
                if test_was_successful:
                    LOGGER.info("Test completed successfully.")
                else:
                    LOGGER.error("Test failed: %s", test_problem_description)
                loop_for_this_test.call_soon_threadsafe(lambda: watchdog_handle.cancel())

                # We give the outer grab_loop_and_run_test a chance to complete
                # before burning the bridge:
                loop_for_this_test.call_soon_threadsafe(lambda: loop_for_this_test.call_later(0.05, lambda: loop_for_this_test.stop()))

        await loop_for_this_test.run_in_executor(None, run_test)

    # We defeat the nikola site building functionality, so this does not actually get called.
    # But the code setting up site building wants a command list:
    command_auto.nikola_cmd = ["echo"]

    # Defeat the site building functionality, and instead insert the test:
    command_auto.run_initial_rebuild = grab_loop_and_run_test

    try:
        # Start the development server
        # which under the hood runs our test when trying to build the site:
        command_auto.execute(options=options)

        # Verify the test succeeded:
        if test_inner_error is not None:
            raise test_inner_error
        assert test_was_successful, test_problem_description
    finally:
        # Nikola is written with the assumption that it can
        # create the event loop at will without ever cleaning it up.
        # As this tests runs several times in succession,
        # that assumption becomes a problem.
        LOGGER.info("Cleaning up loop.")
        # Loop cleanup:
        assert loop_for_this_test is not None
        assert not loop_for_this_test.is_running()
        loop_for_this_test.close()
        asyncio.set_event_loop(None)
        # We would like to leave it at that,
        # but doing so causes the next test to fail.
        #
        # We did not find asyncio - API to reset the loop
        # to "back to square one, as if just freshly started".
        #
        # The following code does not feel right, it's a kludge,
        # but it apparently works for now:
        if sys.platform == 'win32':
            # For this case, the auto module has special code
            # (at module load time! 😟) which we reluctantly reproduce here:
            asyncio.set_event_loop(asyncio.ProactorEventLoop())
        else:
            asyncio.set_event_loop(asyncio.new_event_loop())


@pytest.fixture(scope="module",
                params=["https://example.org",
                        "https://example.org:1234/blog",
                        "https://example.org:3456/blog/",
                        "http://example.org/deep/down/a/rabbit/hole"
                        ])
def site_and_base_path(request) -> Tuple[MyFakeSite, str]:
    """Return a fake site and the base_path (root) the dev server should be serving."""
    assert OUTPUT_FOLDER.is_dir(), \
        f"Could not find dev server test fixture {OUTPUT_FOLDER.as_posix()}"

    config = {
        "post_pages": [],
        "FILES_FOLDERS": [],
        "GALLERY_FOLDERS": [],
        "LISTINGS_FOLDERS": [],
        "IMAGE_FOLDERS": [],
        "SITE_URL": request.param,
        "OUTPUT_FOLDER": OUTPUT_FOLDER.as_posix(),
    }
    return (MyFakeSite(config), auto.base_path_from_siteuri(request.param))


@pytest.fixture(scope="module")
def expected_text():
    """Read the index.html file from the fixture folder and return most of it.

    For life reload, the server will fiddle with HTML <head>,
    so this only returns everything after the opening <body> tag.
    """
    with open(OUTPUT_FOLDER / "index.html", encoding="utf-8") as html_file:
        all_html = html_file.read()
        return all_html[all_html.find("<body>"):]


@pytest.mark.parametrize(("uri", "expected_basepath"), [
    ("http://localhost", ""),
    ("http://local.host", ""),
    ("http://localhost/", ""),
    ("http://local.host/", ""),
    ("http://localhost:123/", ""),
    ("http://local.host:456/", ""),
    ("https://localhost", ""),
    ("https://local.host", ""),
    ("https://localhost/", ""),
    ("https://local.host/", ""),
    ("https://localhost:123/", ""),
    ("https://local.host:456/", ""),
    ("http://example.org/blog", "/blog"),
    ("https://lorem.ipsum/dolet/", "/dolet"),
    ("http://example.org:124/blog", "/blog"),
    ("http://example.org:124/Deep/Rab_bit/hol.e/", "/Deep/Rab_bit/hol.e"),
    # Would anybody in a sane mind actually do this?
    ("http://example.org:124/blog?lorem=ipsum&dol=et", "/blog"),
])
def test_basepath(uri: str, expected_basepath: Optional[str]) -> None:
    assert expected_basepath == auto.base_path_from_siteuri(uri)
