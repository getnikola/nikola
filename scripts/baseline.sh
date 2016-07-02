#!/bin/bash
PYVER=$(./getpyver.py short)
if [[ $PYVER == '3.5' || $PYVER == '2.7' ]]; then
    echo -e "\033[36m>> Downloading baseline for $PYVER...\033[0m"
    # we only support 2.7 and 3.5
    wget https://github.com/getnikola/invariant-builds/archive/v$PYVER'.zip'
    unzip 'v'$PYVER'.zip'
    rm -rf baseline$PYVER
    mv invariant-builds-$PYVER baseline
    rm 'v'$i'.zip'
else
    echo -e "\033[35m>> Version $PYVER does not support baseline testing.\033[0m"
fi
nikola init -qd nikola-baseline-build
cd nikola-baseline-build
cp ../tests/data/1-nolinks.rst posts/1.rst
rm "stories/creating-a-theme.rst" "stories/extending.txt" "stories/internals.txt" "stories/manual.rst" "stories/social_buttons.txt" "stories/theming.rst" "stories/path_handlers.txt" "stories/charts.txt"
LC_ALL='en_US.UTF-8' PYTHONHASHSEED=0 nikola build --invariant
if [[ "$1" == "check" ]]; then
    echo "\033[36m>> Testing baseline...\033[0m"
    diff -ubwr ../baseline output
    if [[ $? == 0 ]]; then
        echo -e "\033[32;1m>> OK\033[0m"
    else
        echo -e "\033[31;1m>> Failed with exit code $?\033[0m"
        exit 1
    fi
fi
