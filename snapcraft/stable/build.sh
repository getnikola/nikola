#!/bin/sh
snapcraft pull
pip3 wheel --wheel-dir parts/nikola/packages --disable-pip-version-check --no-index --find-links parts/nikola/packages pillow
snapcraft build
snapcraft stage
find prime/ -name '*.a' -exec rm {} \;
snapcraft snap

