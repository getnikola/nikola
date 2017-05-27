#!/bin/bash
for i in $@; do
    wget https://github.com/getnikola/wheelhouse/archive/v$i'.zip'
    unzip 'v'$i'.zip'
    pip install --use-wheel --no-index --find-links=wheelhouse-$i lxml Pillow PyYAML
    rm -rf wheelhouse-$i 'v'$i'.zip'
done
