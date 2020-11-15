#!/bin/bash
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
    diff -ubwr ../baseline output
    if [[ $? == 0 ]]; then
        echo -e "\033[32;1m>> Baseline test successful\033[0m"
    else
        CODE=$?
        echo -e "\033[31;1m>> Failed with exit code $CODE\033[0m"
        echo "If this change was intentional, the baseline site needs to be rebuilt (maintainers only). Otherwise, please fix this issue."
        exit $CODE
    fi
fi
