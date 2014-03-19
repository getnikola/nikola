#!/bin/bash
cd tests/data
for i in $@; do
    if [[ $i == '2.7' ]]; then
        # we only support 2.7 now
        wget https://github.com/getnikola/invariant-builds/archive/v$i'.zip'
        unzip 'v'$i'.zip'
        rm -rf baseline$i
        mv invariant-builds-$i baseline$i
        rm 'v'$i'.zip'
    else
        echo 'Version '$i' does not support baseline testing.'
    fi
done
