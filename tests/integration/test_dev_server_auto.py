import asyncio
from typing import Optional, Tuple

import pytest
import requests

import nikola.plugins.command.auto as auto
from nikola.utils import base_path_from_siteuri
from .dev_server_test_helper import MyFakeSite, SERVER_ADDRESS, find_unused_port, TEST_MAX_DURATION, LOGGER, \
    OUTPUT_FOLDER


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
        "no-server": False,
        "poll": False
    }

    # We start an event loop, run the test in an executor,
    # and wait for the event loop to terminate.
    # These variables help to transport the test result to
    # the main thread outside the event loop:
    test_was_successful = False
    test_problem_description = "Async test setup apparently broken"
    test_inner_error: Optional[BaseException] = None
    loop = None

    async def grab_loop_and_run_test() -> None:
        nonlocal test_problem_description, loop

        loop = asyncio.get_running_loop()
        watchdog_handle = loop.call_later(TEST_MAX_DURATION, loop.stop)
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
                loop.call_soon_threadsafe(watchdog_handle.cancel)
                # Simulate Ctrl+C:
                loop.call_soon_threadsafe(lambda: loop.call_later(0.01, loop.stop))

        await loop.run_in_executor(None, run_test)

    # We defeat the nikola site building functionality, so this does not actually get called.
    # But the code setting up site building wants a command list:
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
    return MyFakeSite(config), base_path_from_siteuri(request.param)


@pytest.fixture(scope="module")
def expected_text():
    """Read the index.html file from the fixture folder and return most of it.

    For life reload, the server will fiddle with HTML <head>,
    so this only returns everything after the opening <body> tag.
    """
    with open(OUTPUT_FOLDER / "index.html", encoding="utf-8") as html_file:
        all_html = html_file.read()
        return all_html[all_html.find("<body>"):]
