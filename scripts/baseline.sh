#!/bin/bash

set -e -o pipefail -x

PYVER=$(scripts/getpyver.py short)
if [[ "$1" == "check" ]]; then
    echo -e "\033[36m>> Downloading baseline for $PYVER...\033[0m"
    wget https://github.com/getnikola/invariant-builds/archive/v$PYVER'.zip'
    if [[ $? != 0 ]]; then
        echo -e "\033[31;1m>> Cannot download baseline for $PYVER.\033[0m"
        exit 1
    fi
    unzip -q 'v'$PYVER'.zip'
    rm -rf baseline$PYVER
    mv invariant-builds-$PYVER baseline
    rm 'v'$PYVER'.zip'
fi
nikola init -qd nikola-baseline-build
cd nikola-baseline-build
cp ../tests/data/1-nolinks.rst posts/1.rst
rm "pages/creating-a-theme.rst" "pages/extending.rst" "pages/internals.rst" "pages/manual.rst" "pages/social_buttons.rst" "pages/theming.rst" "pages/path_handlers.rst" "pages/charts.rst"
LC_ALL='en_US.UTF-8' PYTHONHASHSEED=0 nikola build --invariant
if [[ "$1" == "check" ]]; then
    echo -e "\033[36m>> Testing baseline...\033[0m"
    python3 -c '
# In-place edit of copyright notes to adjust the copyright year.
import time
YEAR = str(time.gmtime().tm_year)
for edit_me in [
        "../baseline/rss.xml",
        "../baseline/index.html",
        "../baseline/galleries/index.html",
        "../baseline/galleries/demo/index.html",
        "../baseline/listings/index.html",
        "../baseline/listings/hello.py.html",
        "../baseline/listings/__pycache__/index.html",
        "../baseline/pages/about-nikola/index.html",
        "../baseline/pages/bootstrap-demo/index.html",
        "../baseline/pages/dr-nikolas-vendetta/index.html",
        "../baseline/pages/listings-demo/index.html",
        "../baseline/pages/quickref/index.html",
        "../baseline/pages/quickstart/index.html",
        "../baseline/posts/welcome-to-nikola/index.html",
    ]:
    with open(edit_me, "rt+") as rssf:
        rss = rssf.read()
        copyright_prelude = "Contents © "
        copyright_prelude_position = rss.find(copyright_prelude)
        if -1 == copyright_prelude_position:
            raise RuntimeError(f"Could not find copyright note in {edit_me}")
        copyright_position = copyright_prelude_position + len(copyright_prelude)
        new_rss = rss[:copyright_position] + YEAR + rss[copyright_position+4:]
        rssf.seek(0, 0)
        rssf.write(new_rss)
    '
    if diff -ubwr ../baseline output; then
        echo -e "\033[32;1m>> Baseline test successful\033[0m"
    else
        CODE=$?
        echo -e "\033[31;1m>> Failed with exit code $CODE\033[0m"
        echo "If this change was intentional, the baseline site needs to be rebuilt (maintainers only). Otherwise, please fix this issue."
        exit $CODE
    fi
fi
