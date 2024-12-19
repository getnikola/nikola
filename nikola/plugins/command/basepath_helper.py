import urllib


def base_path_from_siteuri(siteuri: str) -> str:
    """Extract the path part from a URI such as site['SITE_URL'].

    The path never ends with a "/". (If only "/" is intended, it is empty.)
    """
    path = urllib.parse.urlsplit(siteuri).path
    if path.endswith("/"):
        path = path[:-1]
    return path
