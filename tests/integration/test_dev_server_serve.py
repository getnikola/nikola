import logging
import re
import socket
import sys
from io import StringIO
from time import sleep
from typing import Tuple
import requests
import pytest
from concurrent.futures import ThreadPoolExecutor

import nikola.plugins.command.serve as serve
from nikola.utils import base_path_from_siteuri
from .dev_server_test_helper import MyFakeSite, SERVER_ADDRESS, find_unused_port, LOGGER, OUTPUT_FOLDER


def test_server_on_used_port(site_and_base_path: Tuple[MyFakeSite, str]) -> None:
    """Check error if port for nikola serve is already being used.

    `nikola serve` uses a default port and if that port is already in use it should print out a nice
    error message that tells the user what happend and how to fix this.

    To test the case where the port is already in use, we open a socket on the same port that we use
    for `nikola serve` before starting the server.

    The program should exit with a return code of 3 in this case and print out a message to the user.
    """

    site, base_path = site_and_base_path
    site.show_tracebacks = False
    command_serve = serve.CommandServe()
    command_serve.set_site(site)
    command_serve.serve_pidfile = "there is no file with this name we hope"
    command_serve.logger = logging.getLogger("dev_server_test")
    catch_log = StringIO()
    catch_log_handler = logging.StreamHandler(catch_log)
    logging.getLogger().addHandler(catch_log_handler)
    try:
        s = socket.socket()
        try:
            ANY_PORT = 0
            s.bind((SERVER_ADDRESS, ANY_PORT))
            address, port = s.getsockname()
            with ThreadPoolExecutor(max_workers=2) as executor:
                options = {
                    "address": SERVER_ADDRESS,
                    "port": port,
                    "browser": False,
                    "detach": False,
                    "ipv6": False,
                }
                future_to_run_web_server = executor.submit(lambda: command_serve.execute(options=options))
                command_serve.shutdown()
                result = future_to_run_web_server.result()
                assert 3 == result

                # TODO: check if this works on windows
                # for now we skip this assert on windows platforms.
                if not sys.platform == 'win32':
                    assert re.match(
                        r"Port address \d+ already in use, "
                        r"please use the `\-p \<port\>` option to select a different one\.",
                        catch_log.getvalue()
                    )
                assert "OSError" not in catch_log.getvalue()
        finally:
            s.close()
    finally:
        logging.getLogger().removeHandler(catch_log_handler)


def test_serves_root_dir(
    site_and_base_path: Tuple[MyFakeSite, str], expected_text: str
) -> None:
    site, base_path = site_and_base_path
    command_serve = serve.CommandServe()
    command_serve.serve_pidfile = "there is no file with this name we hope"
    command_serve.logger = logging.getLogger("dev_server_test")
    command_serve.set_site(site)
    options = {
        "address": SERVER_ADDRESS,
        "port": find_unused_port(),
        "browser": False,
        "detach": False,
        "ipv6": False,
    }

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_to_run_web_server = executor.submit(lambda: command_serve.execute(options=options))
        try:
            sleep(0.05)  # Wait for the web server to start up.
            with requests.Session() as session:
                server_root_uri = f"http://{options['address']}:{options['port']}"

                # Grab the document root index.html file:
                server_base_uri = f"{server_root_uri}{base_path}"
                LOGGER.info("Attempting to fetch HTML from %s", server_base_uri)
                res = session.get(server_base_uri)
                res.raise_for_status()
                assert "text/html; charset=UTF-8" == res.headers['content-type']
                text_found = res.text.replace("\r\n", "\n")  # On windows, the server provides spurious \r
                assert expected_text == text_found

                assert not base_path.endswith("/")
                res2 = session.get(f"{server_root_uri}{base_path}/")
                res2.raise_for_status()
                assert "text/html; charset=UTF-8" == res2.headers['content-type']
                text_found_2 = res2.text.replace("\r\n", "\n")
                assert expected_text == text_found_2

                res3 = session.get(f"{server_root_uri}{base_path}/index.html")
                res3.raise_for_status()
                assert "text/html; charset=UTF-8" == res3.headers['content-type']
                text_found_3 = res3.text.replace("\r\n", "\n")
                assert expected_text in text_found_3

            LOGGER.info("Web server access successful with intended result.")
        finally:
            LOGGER.info("Asking the webserver to shut down")
            command_serve.shutdown()
            future_to_run_web_server.result()
            LOGGER.info("Webserver shut down successfully.")
    LOGGER.info("Threadpool closed.")


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
        "OUTPUT_FOLDER": OUTPUT_FOLDER.as_posix(),
        # See https://github.com/getnikola/nikola/issues/3802
        # "SITE_URL": request.param,
        "BASE_URL": request.param
    }
    return MyFakeSite(config), base_path_from_siteuri(request.param)


@pytest.fixture(scope="module")
def expected_text():
    """Read the index.html file from the fixture folder and return it.
    """
    with open(OUTPUT_FOLDER / "index.html", encoding="utf-8") as html_file:
        return html_file.read()


@pytest.mark.parametrize("basepath,path,expected_result", [
    ("/huba/", "/huba/buba", "/buba"),
    ("/huba/", "/huba/", "/"),
    ("/ping/pong/", "/ping/pong", "/"),
    ("/huba/", "/huba/lorem/ipsum.txt", "/lorem/ipsum.txt"),
    ("/", "/huba/buba", "/huba/buba")
])
def test_path_omitted(basepath, path, expected_result) -> None:
    assert expected_result == serve._omit_basepath_component(basepath, path)
