#!/bin/sh
rm -rf parts/ stage/ prime/
snapcraft pull
pip3 wheel --wheel-dir parts/nikola/packages --disable-pip-version-check --no-index --find-links parts/nikola/packages pillow
snapcraft

