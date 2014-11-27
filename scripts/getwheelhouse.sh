#!/bin/bash
for i in $@; do
    wget https://github.com/getnikola/wheelhouse/archive/v$i'.zip'
    unzip 'v'$i'.zip'
    pip install --use-wheel --no-index --find-links=wheelhouse-$i lxml Pillow ipython
    # Install Markdown for Python 2.6.
    pip install --use-wheel --no-index --find-links=wheelhouse-$i Markdown || true
    rm -rf wheelhouse-$i 'v'$i'.zip'
done
